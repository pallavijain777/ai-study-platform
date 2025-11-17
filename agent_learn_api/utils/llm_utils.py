import os
import openai
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains.llm_math.base import LLMMathChain

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")
model = ChatOpenAI(model="gpt-4o", temperature=0.9)

def solve_math(query: str) -> str:
    """
    Use langchain's llmmath chain to solve math problems
    """
    chain = LLMMathChain.from_llm(model)
    try:
        return chain.run(query)
    except Exception as e:
        return f"Error: {str(e)}"
    
def normal_llm_answer(query: str) -> str:
    return model.invoke(query).content