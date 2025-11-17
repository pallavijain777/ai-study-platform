import os
import openai
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0.9)


class TreeMapNode(BaseModel):
    label: str = Field(description="The label describing the node topic")
    children: List["TreeMapNode"] = Field(default_factory=list)

    def find(self, label: str):
        if self.label == label:
            return self
        for child in self.children:
            found = child.find(label)
            if found:
                return found
        return None

    def get_dict(self):
        return {
            "label": self.label,
            "children": [child.get_dict() for child in self.children],
        }


class TreeMapNodeList(BaseModel):
    contents: List["TreeMapNode"] = Field(description="List of nodes at a level")


class TreeMapBuilder:
    def __init__(self, root: Optional[TreeMapNode] = None):
        self.root = root

    def add_root(self, root: TreeMapNode):
        self.root = root

    def add_to_parent(self, parent_label: str, child_label: str):
        parent_node = self.root.find(parent_label)
        if not parent_node:
            raise ValueError(f"Parent '{parent_label}' not found")
        child = TreeMapNode(label=child_label)
        parent_node.children.append(child)
        return child

    def show(self):
        return self.root.get_dict()


def generate_mindmap(main_topic: Optional[str], topic: str, depth: int = 2) -> TreeMapBuilder:
    parser = PydanticOutputParser(pydantic_object=TreeMapNodeList)
    builder = TreeMapBuilder(TreeMapNode(label=topic))

    template = """
    You are an expert mindmap builder.
    Generate a JSON array of main subtopics for {topic}.
    The main topic around which you are building is {main_topic}.
    Return only valid JSON matching this schema:
    {format_instructions}
    """

    prompt = PromptTemplate(
        template=template,
        input_variables=["topic", "main_topic"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | model | parser
    answer = chain.invoke({"topic": topic, "main_topic": main_topic})

    for item in answer.contents:
        builder.add_to_parent(topic, item.label)

    if depth > 1:
        for item in answer.contents:
            sub_builder = generate_mindmap(main_topic, item.label, depth - 1)
            node = builder.root.find(item.label)
            if node:
                node.children.extend(sub_builder.root.children)
                
    print(builder.show())
    return builder

          