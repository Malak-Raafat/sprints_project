import asyncio
import os
import json
from fastapi import FastAPI, Form, Query, Request, HTTPException # type: ignore
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from starlette.middleware.sessions import SessionMiddleware # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from agents.research_agent import fetch_arxiv_papers
from agents.analysis_agent import analyze_papers
from agents.innovation_agent import generate_research_idea, format_innovation_proposal
from agents.innovation_agent import save_proposal_as_markdown  # type: ignore
from agents.database import init_db, get_db_connection
from fastapi.responses import RedirectResponse  # type: ignore
from fastapi import Request   # type: ignore
from starlette.concurrency import run_in_threadpool # type: ignore
from fastapi.responses import FileResponse  # type: ignore



# === FastAPI App ===
app = FastAPI(title="Gen AI Adaptive Research Agent Ecosystem")
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/static/index.html", include_in_schema=False)
def static_index(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/login-page")
    return FileResponse("static/index.html")


@app.get("/static/{file_name}", include_in_schema=False)
def block_sensitive_static(file_name: str, request: Request):
    if file_name == "index.html" and "user" not in request.session:
        return RedirectResponse(url="/login-page")
    return FileResponse(os.path.join("static", file_name))

# === Serve Pages ===

@app.get("/", include_in_schema=False)
def home(request: Request):
    if request.session.get("user"):
        return FileResponse("static/index.html")
    return RedirectResponse("/login-page")



@app.get("/check-session")
def check_session(request: Request):
    if request.session.get("user"):
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Not logged in")


@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    if "user" in request.session:
        return RedirectResponse("/")
    return FileResponse("static/login.html")

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login-page")


# === Auth Handlers ===

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    raise HTTPException(status_code=401, detail="❌ Invalid credentials")

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return RedirectResponse("/login-page", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"❌ User already exists or DB error: {e}")
    finally:
        conn.close()


# === Config Handling ===

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"topic": "AI", "max_results": 5}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


@app.post("/set-config")
def set_config(request: Request, topic: str = Form(...), max_results: int = Form(...)):
    if "user" not in request.session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if int(max_results) > 100:
        raise HTTPException(status_code=400, detail="Max results cannot exceed 100")

    config = {"topic": topic, "max_results": int(max_results)}
    save_config(config)
    return {"message": "✅ Config updated", "config": config}

# === Background Task ===

fetched_papers_background = []

async def fetch_papers_loop():
    global fetched_papers_background
    while True:
        try:
            config = load_config()
            topic = config.get("topic", "AI")
            max_results = config.get("max_results", 5)
            papers = fetch_arxiv_papers(topic=topic, max_results=max_results)
            fetched_papers_background = papers
            print(f"[Background] ✅ Fetched {len(papers)} papers for topic: {topic}")
        except Exception as e:
            print(f"[Background Error] ❌ {e}")
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(fetch_papers_loop())

@app.get("/run-agents")
def run_agents(request: Request, topic: str = Query("gen ai"), max_results: int = Query(5)):
    check_auth(request)

    from agents.research_agent import fetch_arxiv_papers
    from agents.analysis_agent import analyze_from_bus
    from agents.innovation_agent import generate_from_bus
    print("[RUN AGENTS] ✅ Papers, keywords, and proposal generated")

    fetch_arxiv_papers(topic, max_results)
    analyze_from_bus()
    proposal = generate_from_bus()

    return {"topic": topic, "proposal": proposal}

# === API Endpoints ===

def check_auth(request: Request):
    if "user" not in request.session:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/fetch-papers")
def fetch_papers(request: Request, topic: str = Query("AI"), max_results: int = Query(5)):
    check_auth(request)
    papers = fetch_arxiv_papers(topic=topic, max_results=max_results)
    return {"topic": topic, "results": papers}

@app.get("/analyze")
def analyze(request: Request, topic: str = Query("AI"), max_results: int = Query(5)):
    check_auth(request)
    try:
        papers = fetch_arxiv_papers(topic=topic, max_results=max_results)

        if len(papers) > 20:
            papers = papers[:20]  
        keywords = analyze_papers(papers)
        return {"topic": topic, "top_keywords": keywords}
    except Exception as e:
        import traceback
        print("🚨 [Analyze Error]", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error during keyword analysis")
@app.get("/innovate")
def innovate(request: Request, topic: str = Query("AI"), max_results: int = Query(5)):
    check_auth(request)

    papers = fetch_arxiv_papers(topic=topic, max_results=max_results)
    keywords = [kw for kw, _ in analyze_papers(papers)]
    raw = generate_research_idea(keywords)
    formatted = format_innovation_proposal(raw)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO proposals (user_id, topic, keywords, proposal_text)
        VALUES ((SELECT id FROM users WHERE username = ?), ?, ?, ?)
        """,
        (request.session["user"], topic, json.dumps(keywords), raw)
    )
    proposal_id = cursor.lastrowid 
    conn.commit()
    conn.close()

    return {
        "topic": topic,
        "proposal": formatted,
        "proposal_id": proposal_id  
    }



@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Serve the chat interface"""
    return FileResponse("static/chat.html")

@app.post("/chat")
async def handle_chat(request: Request, data: dict):
    """Handle chat messages and generate responses"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    message = data.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, message, is_user) VALUES ("
        "(SELECT id FROM users WHERE username=?), ?, 1)",
        (user, message)
    )
    conn.commit()
    
    response, proposal_id = await process_with_agents(user, message)
    
    cursor.execute(
        "INSERT INTO chat_history (user_id, message, is_user) VALUES ("
        "(SELECT id FROM users WHERE username=?), ?, 0)",
        (user, response)
    )
    conn.commit()
    conn.close()
    
    return {"response": response, "proposal_id": proposal_id}

@app.post("/feedback")
async def handle_feedback(request: Request, data: dict):
    """Store user feedback on proposals"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    proposal_id = data.get("proposal_id")
    rating = data.get("rating")
    
    if not proposal_id or rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Invalid feedback data")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE proposals SET rating=? WHERE id=? AND user_id="
        "(SELECT id FROM users WHERE username=?)",
        (rating, proposal_id, user)
    )
    conn.commit()
    conn.close()
    
    return {"status": "success"}


async def process_with_agents(username: str, message: str):
    message = message.lower()
    config = load_config()
    max_results = config.get("max_results", 5)

    if any(keyword in message for keyword in ["research", "papers", "find", "article", "paper", "about", "ai", "ml", "deep learning", "gen ai"]):
        papers = await run_in_threadpool(fetch_arxiv_papers, topic=config["topic"], max_results=max_results)
        response = f"I found {len(papers)} recent papers:\n"
        response += "\n".join(f"- {p['title']}" for p in papers)
        return response, None

    elif any(keyword in message for keyword in ["idea", "proposal", "generate", "innovation"]):
        papers = await run_in_threadpool(fetch_arxiv_papers, topic=config["topic"], max_results=max_results)
        
        if not papers:
            return "❌ No papers found to generate a proposal.", None

        keywords = await run_in_threadpool(analyze_papers, papers)

        if not keywords or len(keywords) < 2:
            return "❌ Not enough keywords extracted to generate a meaningful proposal.", None

        try:
            proposal = await run_in_threadpool(generate_research_idea, keywords)
            formatted = await run_in_threadpool(format_innovation_proposal, proposal)
        except Exception as e:
            print("❌ Innovation generation failed:", e)
            return "❌ Failed to generate proposal. Please try again with a broader topic.", None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO proposals (user_id, topic, keywords, proposal_text) VALUES ("
            "(SELECT id FROM users WHERE username=?), ?, ?, ?)",
            (username, config["topic"], json.dumps(keywords), proposal)
        )
        proposal_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return formatted, proposal_id


    elif any(keyword in message for keyword in ["analyze", "trends", "trend", "pattern", "analysis"]):
        papers = await run_in_threadpool(fetch_arxiv_papers, topic=config["topic"], max_results=max_results)
        keywords = await run_in_threadpool(analyze_papers, papers)
        response = "Top keywords and trends:\n" + "\n".join(f"- {k[0]} ({k[1]})" for k in keywords)
        return response, None

    else:
        return (
            "I'm a research assistant. You can ask me to:\n"
            "- Find recent research papers\n"
            "- Generate research proposals\n"
            "- Analyze trends in a field"
        ), None


@app.get("/export-report")
def export_report(request: Request):
    check_auth(request)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT topic, keywords, proposal_text FROM proposals WHERE user_id=(SELECT id FROM users WHERE username=?) ORDER BY id DESC LIMIT 1",
        (request.session["user"],)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No proposals found")

    topic, keywords, proposal_text = row
    filename = save_proposal_as_markdown(topic, json.loads(keywords), proposal_text)
    return FileResponse(filename, media_type='text/markdown', filename="latest_proposal.md")
