#  Gen AI Adaptive Research Agent Ecosystem

An intelligent web-based platform that automates academic research discovery, trend analysis, and research idea generation using generative AI. 
Built with FastAPI, LangChain, Groq, and SQLite, the system features a modular multi-agent backend, interactive dashboard, secure login, and a chatbot research assistant.

---

## Features

-  User registration and login system
-  Fetch recent papers from arXiv API
-  Analyze top research trends using keyword extraction
-  Generate structured research proposals using LLaMA-3.3 (Groq API)
-  Chat-based interaction with an AI research assistant
-  Download latest research proposal in Markdown
-  Submit feedback for proposals
-  Agents communicate via an internal message bus
-  Local database (SQLite3) for user data, chat logs, and proposals

---

##  Project Structure
adaptive_agent/
├── agents/
│ ├── analysis_agent.py
│ ├── database.py
│ ├── innovation_agent.py
│ ├── message_bus.py
│ └── research_agent.py
├── static/
│ ├── index.html
│ ├── login.html
│ └── chat.html
├── config.json
├── proposal.md
├── main.py


Testing (Manual)
You can test each component by visiting these endpoints:

/fetch-papers?topic=ai&max_results=5
/analyze?topic=ai&max_results=5
/innovate?topic=ai&max_results=5
/chat-ui
/export-report to download your proposal

Modular Agent Design
Module	Description
research_agent.py	Fetches papers from arXiv API
analysis_agent.py	Extracts top keywords using word frequency
innovation_agent.py	Uses Groq + LangChain to generate proposals
message_bus.py	Simulates pub-sub message communication
database.py	Initializes and connects to SQLite3 DB

Dependencies
FastAPI
Uvicorn
LangChain
Groq
Requests
SQLite3



Open PowerShell
Navigate to the project folder:
PS C:\Users\Ahmed Raafat> cd adaptive_agent # write this
Run the FastAPI server using Uvicorn
Start the backend API server with auto-reload enabled:
PS C:\Users\Ahmed Raafat\adaptive_agent> python -m uvicorn main:app --reload  # write this
Expected Console Output
If everything is set up correctly, you will see the following output:

INFO:     Will watch for changes in these directories: ['C:\\Users\\Ahmed Raafat\\adaptive_agent']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [19424] using WatchFiles
INFO:     Started server process [28200]
INFO:     Waiting for application startup.
[BUS] Published: papers
[Background] ✅ Fetched 3 papers for topic: Quantum Computing
Access the Application in Your Browser
Open your browser and go to:

🔑 Login Page: http://127.0.0.1:8000/login-page
🧠 Dashboard: http://127.0.0.1:8000/static/index.html
💬 Chat UI: http://127.0.0.1:8000/chat-ui

