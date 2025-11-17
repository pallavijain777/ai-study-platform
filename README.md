# 🚀 AI-Powered EdTech Platform  
### Multi-Agent Learning System built with **Python, LangChain, LangGraph & OpenAI**

This project is a fully-featured **AI-driven EdTech platform** designed to deliver deeply personalized and interactive learning experiences.  
It combines **multi-agent orchestration**, intelligent content generation, vector-based retrieval, and topic-based workspaces to create a complete end-to-end AI learning environment.

This system demonstrates strong expertise in **Generative AI engineering, multi-agent design, RAG (Retrieval-Augmented Generation), LLM-driven workflows, and full-stack AI product development.**

Perfect for showcasing advanced AI capabilities to clients and companies.

---

## 🌟 Key Capabilities

### **1. Topic-Focused Workspaces**  
Each user receives independent learning workspaces for every subject or topic.  
All actions — **chat, documents, quizzes, mind maps, images** — stay isolated and context-aware.

---

### **2. Intelligent Chat with Memory**  
Conversation history stored per workspace.  
Powered by a dedicated **Chat Agent (LLM)**.

The agent:
- Explains complex concepts  
- Solves tough math problems  
- Helps with logic, reasoning, and theory  
- Acts like a personal AI tutor

---

### **3. Smart Document Uploading + RAG**  
Users can upload notes, PDFs, or reference documents.  
Uploaded files are indexed using **FAISS Vector Database**.

Benefits:
- Accurate, context-aware answers  
- Personalized learning from user data  
- Retrieval-Augmented Generation (RAG) pipeline

---

### **4. Automatic Quiz Generation & Analysis**  
A specialized **Quiz Agent** generates:
- MCQs  
- Conceptual questions  
- Explanations  
- Performance analysis  

Ideal for self-assessment and learning reinforcement.

---

### **5. AI-Generated Mind Maps**  
Using **LangChain’s Pydantic Output Parser**, the system produces clean, hierarchical mind maps for any topic or sub-topic.

Perfect for visual learners.

---

### **6. AI-Generated PDFs & Images**  
The **Document Agent** creates:
- Structured study notes  
- Summaries  
- Explanatory documents  
- Downloadable PDFs (via **FPDF**)  
- Images and diagrams (via **Hugging Face** diffusion models)

---

### **7. Web Search Enhanced Learning**  
A **Web Agent** performs real-time Google searches to gather:
- Latest information  
- Verified sources  
- Context beyond existing documents  

Allows dynamic and up-to-date knowledge retrieval.

---

## 🤖 Multi-Agent Architecture

This platform uses a **LangGraph multi-agent system**, where each agent specializes in a specific learning function.

| **Agent** | **Role / Responsibilities** |
|----------|------------------------------|
| **Chat Agent (LLM)** | General chat, tutoring, conceptual explanations, solving math problems |
| **Web Agent** | Performs Google searches, retrieves fresh knowledge |
| **Document Agent** | Creates study notes, summaries, PDFs, explanations |
| **Quiz Agent** | Generates quizzes, MCQs, detailed explanations |
| **Mind Map Agent** | Generates structured, hierarchical mind maps |
| **RAG Agent (Internal)** | Handles vector search using FAISS |

---

## 🛠️ Tech Stack

### **Core AI & Orchestration**
- Python 
- LangChain  
- LangGraph  
- OpenAI API (ChatGPT / GPT-4 / GPT-4o)

### **Vector Search & Processing**
- FAISS Vector Database  
- PyTorch  

### **Document & Media Generation**
- FPDF (PDF creation)  
- Hugging Face Diffusion Models (image generation)  

### **Backend**
- Flask  

---

## 📌 Highlighted Features (At a Glance)

- Multi-Agent AI Learning System  
- Topic-based Workspaces  
- Conversation Memory  
- Quiz Generator + Explanations  
- Mind Map Generator  
- PDF + Image Creation  
- Google Search Integrated Agent  
- FAISS Vector Search (RAG Pipeline)  
- Modular + Scalable Architecture  
