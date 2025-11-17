import os
import openai
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from agent_learn_api.utils.document_utils import *
from agent_learn_api.utils.google_utils import *
from agent_learn_api.utils.llm_utils import *
from agent_learn_api.utils.quiz_utils import *
from agent_learn_api.utils.treemap_utils import *
from agent_learn_api.models.chat import Chat
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import Tool
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser , StrOutputParser
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

# --- Setup ---
load_dotenv(find_dotenv())
openai.api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(temperature=0.9, model="gpt-4o")

# --- State models ---
class AgentBase(BaseModel):
    input: str
    chat_history: list = []
    route: str | None = None
    next_inputs: dict | None = None
    messages: list = []  # LangGraph expects this
    output: str | None = None 


class RouterOutput(BaseModel):
    destination: str = Field(description="Name of the destination agent")
    next_inputs: dict = Field(description="Inputs to forward to the agent")
    
class ToolCall(BaseModel):
    tool: str = Field(description="The tool to call (or 'NONE' if no tool)")
    tool_input: str = Field(description="The input or final answer")

# --- Delegation between agents ---
def delegate_to_agent(agent_name: str, query: str, agents_map: dict):
    """Delegate a query to another agent and safely return string output."""
    target = agents_map.get(agent_name)
    if not target:
        return f"[Error] Unknown agent '{agent_name}'"

    try:
        # invoke with message-based input for LangGraph compatibility
        response = target.invoke({"messages": [HumanMessage(content=query)]})

        # Normalize the result into plain text
        if isinstance(response, dict):
            if "output" in response and isinstance(response["output"], str):
                return response["output"]
            elif "messages" in response and isinstance(response["messages"], list):
                # flatten message contents if returned as messages
                return "\n".join(
                    [m.content for m in response["messages"] if hasattr(m, "content")]
                )
            else:
                return str(response)

        elif hasattr(response, "content"):
            return response.content

        return str(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"[Error delegating to {agent_name}]: {e}"

def get_delegation_tools(agents_map: dict):
    tools = []
    for n in agents_map.keys():
        tools.append(
            Tool(
                name=f"Delegate to {n.replace('_', ' ').title()}",
                func=lambda q, tgt=n: delegate_to_agent(tgt, q, agents_map),
                description=f"Send this query to the {n.replace('_', ' ').title()} agent for assistance."
            )
        )
    return tools

# --- Chat history loader ---
def load_chat_history(user_id: int, workspace_id: int):
    history = []
    chats = (
        Chat.query.filter_by(user_id=user_id, workspace_id=workspace_id)
        .order_by(Chat.created_at.asc())
        .all()
    )
    for chat in chats:
        if chat.role == "user":
            history.append(HumanMessage(content=chat.content))
        else:
            history.append(AIMessage(content=chat.content))
    return history

# --- Core LLM call ---
def call_llm(state: AgentBase, tool_list):
    tool_names = [t.name for t in tool_list]

    prompt = PromptTemplate(
        template="""
        You are an agent. You can either:
        - Call a tool from this list: {tool_names}
        - Or answer directly if no tool is required.

        If a tool is required, return JSON:
        {{"tool": "<tool name>", "tool_input": "<query>"}}

        If no tool is required, return JSON:
        {{"tool": "NONE", "tool_input": "<final answer>"}}

        User input: {input}
        """,
        input_variables=["input"],
        partial_variables={"tool_names": ", ".join(tool_names)},
    )

    parser = JsonOutputParser(pydantic_object=ToolCall)
    chain = prompt | model | parser

    raw = chain.invoke({"input": state.input})

    # ✅ Force into ToolCall object
    if isinstance(raw, dict):
        parsed = ToolCall.parse_obj(raw)
    else:
        parsed = raw

    if parsed.tool == "NONE":
        return {**state.model_dump(), "output": parsed.tool_input}

    tool = next((t for t in tool_list if t.name == parsed.tool), None)
    if tool:
        try:
            raw_result = tool.func(parsed.tool_input)
            if isinstance(raw_result, list):
                summarizer = (
                    PromptTemplate.from_template(
                        "Summarize the following search results into a single clear answer:\n\n{snippets}"
                    )
                    | model
                    | StrOutputParser()
                )
                result = summarizer.invoke({"snippets": "\n".join(str(r) for r in raw_result)})
            else:
                result = str(raw_result)
        except Exception as e:
            result = f"[Tool {parsed.tool} failed: {e}]"
    else:
        result = f"[Unknown tool {parsed.tool}]"

    return {**state.model_dump(), "output": result}


# --- Agent builder ---
def build_agent(tool_list: list, agents_map):
    # Add delegation tools too
    for tool in get_delegation_tools(agents_map):
        tool_list.append(tool)

    builder = StateGraph(AgentBase)

    # Wrap call_llm with tool_list baked in
    builder.add_node("call_llm", lambda state: call_llm(state, tool_list))

    # Tools node (not really used now, since call_llm executes tools itself)
    def passthrough(state: AgentBase):
        return state.model_dump()
    builder.add_node("tools", passthrough)

    # If LLM decides no tool → END
    # If LLM decides a tool → call_llm handles execution and we still END
    builder.add_edge("call_llm", END)
    builder.add_edge(START, "call_llm")

    return builder.compile(checkpointer=MemorySaver())



# --- Specific agents ---
def create_document_agent(workspace_id: int, user_id: int, agents_map: dict):
    retriever = get_retriever(workspace_id)
    doc_tools = [
        Tool(
            name="PDF creation",
            func=lambda topic: generate_pdf(topic, workspace_id),
            description="Used when the user asks to create documents or PDFs."
        ),
        Tool(
            name="Image creation",
            func=lambda topic: generate_image(topic, workspace_id, 4, (512, 512)),
            description="Used when the user asks to generate images."
        ),
    ]
    if retriever:
        doc_tools.append(
            Tool(
                name="Document search",
                func=lambda q: retriever.get_relevant_documents(q),
                description="Retrieve and answer using workspace documents. Also retrieve them for summaries"
            )
        )
    return build_agent(doc_tools, agents_map)

def create_google_agent(workspace_id: int, user_id: int, agents_map: dict):
    google_tools = [
        Tool(
            name="Google search",
            func=lambda q: google_search(q),
            description="Used when external web search is needed."
        )
    ]
    return build_agent(google_tools, agents_map)

def create_llm_agent(workspace_id: int, user_id: int, agents_map: dict):
    llm_tools = [
        Tool(
            name="Normal answers",
            func=lambda q: normal_llm_answer(q),
            description="Used for general conversational replies."
        ),
        Tool(
            name="Math solving",
            func=lambda q: solve_math(q),
            description="Used for solving math and computation tasks."
        )
    ]
    return build_agent(llm_tools, agents_map)

def create_quiz_agent(workspace_id: int, user_id: int, agents_map: dict):
    quiz_tools = [
        Tool(
            name="Quiz generation",
            func=lambda topic: generate_quiz(5, topic),
            description="Used when the user asks to generate a quiz."
        )
    ]
    return build_agent(quiz_tools, agents_map)

def create_treemap_agent(workspace_id: int, user_id: int, agents_map: dict):
    tree_tools = [
        Tool(
            name="Mindmap generation",
            func=lambda topic: generate_mindmap(topic, 2),
            description="Used when the user asks to generate a mindmap or flowchart."
        )
    ]
    return build_agent(tree_tools, agents_map)

# --- Build agents map ---
def get_agents(workspace_id: int, user_id: int):
    agents_map = {name: None for name in ["doc_agent", "google_agent", "llm_agent", "quiz_agent", "mindmap_agent"]}

    agents_map["doc_agent"] = create_document_agent(workspace_id, user_id, agents_map)
    agents_map["google_agent"] = create_google_agent(workspace_id, user_id, agents_map)
    agents_map["llm_agent"] = create_llm_agent(workspace_id, user_id, agents_map)
    agents_map["quiz_agent"] = create_quiz_agent(workspace_id, user_id, agents_map)
    agents_map["mindmap_agent"] = create_treemap_agent(workspace_id, user_id, agents_map)

    return agents_map

# --- Router ---
def get_router():
    destinations = [
        "quiz_agent",
        "doc_agent",
        "mindmap_agent",
        "google_agent",
        "chat_agent"
    ]
    destinations_str = "\n".join(destinations)

    # ✅ Parser ensures we always get {destination, next_inputs}
    output_parser = PydanticOutputParser(pydantic_object=RouterOutput)

    router_prompt = PromptTemplate(
        template="""
        You are a router. Choose one destination from this list:
        {destinations_str}

        Return JSON with keys 'destination' and 'next_inputs'.
        Example:
        {{"destination": "quiz_agent", "next_inputs": {{"input": "some text"}}}}

        User Input: {input}
        """,
        input_variables=["input"],
        partial_variables={"destinations_str": destinations_str},
    )

    # ✅ RunnableSequence: Prompt → Model → Pydantic parser
    router_chain = router_prompt | model | output_parser
    return router_chain


def get_router_node():
    router_chain = get_router()

    def router_node(state: AgentBase):
        raw: RouterOutput = router_chain.invoke({"input": state.input})
        state.route = raw.destination
        state.next_inputs = raw.next_inputs
        return state

    return router_node

# --- Routing graph ---
def build_routing_graph(workspace_id: int, user_id: int):
    agent_map = get_agents(workspace_id=workspace_id, user_id=user_id)
    builder = StateGraph(AgentBase)

    builder.add_node("router", get_router_node())
    for name, agent in agent_map.items():
        builder.add_node(name, agent)

    builder.add_conditional_edges("router", lambda s: s.route)
    for node in agent_map.keys():
        builder.add_edge(node, END)
    builder.add_edge(START, "router")

    return builder.compile()

# --- Run agent ---
def run_agent(workspace_id: int, user_id: int, query: str):
    history = load_chat_history(user_id=user_id, workspace_id=workspace_id)
    agent = build_routing_graph(workspace_id=workspace_id, user_id=user_id)

    # Construct proper LangGraph state
    state = {
        "input": query,
        "chat_history": history,
        "messages": [HumanMessage(content=query)]
    }

    try:
        result = agent.invoke(state)
        print("✅ Agent result:", result)
        return result.get("output", str(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Detailed Agent error:", str(e))
        return f"Agent error: {e}"
