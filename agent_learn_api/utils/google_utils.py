import os
import openai
import requests
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SEARCH_URL = "https://google.serper.dev/search"
model = ChatOpenAI(model="gpt-4o", temperature=0.9)

def google_search(query: str):
    """
    Perform a Google-like search using Serper API.
    Returns top 3 snippets.
    """
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query}

    response = requests.post(SEARCH_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return [f"Google search failed: {response.text}"]

    data = response.json()
    results = data.get("organic", [])
    return [r["snippet"] for r in results[:3]]