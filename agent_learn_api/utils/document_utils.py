import os
import base64
import torch
from fpdf import FPDF
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from diffusers import StableDiffusionPipeline
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import Docx2txtLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

load_dotenv(find_dotenv())

INDEX_DIR = "indexes"
embeddings = OpenAIEmbeddings()
vision_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def ocr_image(file_path: str) -> str:
    """Extract text + description from an image using GPT-4o Vision."""
    with open(file_path, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode("utf-8")

    response = vision_llm.invoke([
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract visible text and summarize notes/diagrams."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                }
            ]
        }
    ])
    return response.content

def load_pipe():
    pipe = StableDiffusionPipeline.from_pretrained(
        "stabilityai/sd-turbo",
        torch_dtype=torch.float32,  # use float16 only if GPU available
    ).to("cpu")
    return pipe

# Create global instance to reuse
pipe = load_pipe()

def generate_image(prompt: str, workspace_id: int, steps: int = 4, size=(512, 512)):
    base = "generated_docs"
    workspace_folder = os.path.join(base, str(workspace_id))
    os.makedirs(workspace_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = prompt[:30].replace(" ", "_").replace("/", "_")  # optional short name
    file_name = f"{safe_prompt}_{timestamp}.png"
    file_path = os.path.join(workspace_folder, file_name)
    width, height = size
    result = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_inference_steps=steps,
        guidance_scale=0.0
    )
    image = result.images[0]
    image.save(file_path)
    
    return file_name

def generate_pdf(topic: str, workspace_id: int):
    answer = vision_llm.invoke(f"Generate a summary on {topic}").content
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in answer.split('\n'):
        pdf.multi_cell(0, 10, line)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prompt = topic[:30].replace(" ", "_").replace("/", "_")
    file_name = f"{safe_prompt}_{timestamp}.pdf"

    # ✅ Create workspace folder if it doesn’t exist
    folder_path = f"D:\\Aarav\\Aarav\\agent-learn\\generated_docs\\{str(workspace_id)}"
    os.makedirs(folder_path, exist_ok=True)

    # ✅ Save PDF safely
    pdf.output(os.path.join(folder_path, file_name))

    return file_name

            

def load_document(file_path: str) -> list[Document]:
    """Load a text-based document into LangChain format."""
    if file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    elif file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".docx") or file_path.endswith(".doc"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported text file type: {file_path}")
    return loader.load()


def build_faiss_index(docs: list[Document]) -> FAISS:
    return FAISS.from_documents(docs, embeddings)


def save_faiss_index(faiss_index: FAISS, workspace_id: int):
    path = os.path.join(INDEX_DIR, str(workspace_id))
    os.makedirs(path, exist_ok=True)
    faiss_index.save_local(path)


def load_faiss_index(workspace_id: int) -> FAISS | None:
    path = os.path.join(INDEX_DIR, str(workspace_id))
    if not os.path.exists(path):
        return None
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)


def add_to_index(file_path: str, workspace_id: int, extra_text: str | None = None):
    """
    Load a document or image and add it to the FAISS index.
    """
    docs = []
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".txt", ".pdf", ".docx", ".doc"]:
        docs = load_document(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        if not extra_text:
            extra_text = ocr_image(file_path)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.create_documents([extra_text], metadatas=[{"source": file_path}])
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    index = load_faiss_index(workspace_id)
    if index:
        index.add_documents(docs)
    else:
        index = build_faiss_index(docs)

    save_faiss_index(index, workspace_id)


def get_retriever(workspace_id: int):
    index = load_faiss_index(workspace_id)
    if not index:
        return None
    return index.as_retriever(search_kwargs={"k": 5})
