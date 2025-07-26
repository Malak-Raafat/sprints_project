# agents/innovation_agent.py
import os
from typing import List
from agents.message_bus import bus  # ✅ shared bus # type: ignore 
from langchain_groq import ChatGroq  # type: ignore
from langchain_core.prompts import ChatPromptTemplate  # type: ignore

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is missing")

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0,
)

proposal_prompt = ChatPromptTemplate.from_template("""
You are an AI research assistant. Generate a detailed research proposal using these keywords:

Keywords: {keywords}
                                  
Write a concise but informative research proposal incorporating these keywords.
""")
def generate_research_idea(keywords: List[str]) -> str:
    if not keywords:
        return "❌ No keywords provided."

    keywords_str = ", ".join(keywords)
    prompt_input = {"keywords": keywords_str}

    try:
        result = llm.invoke(proposal_prompt.format_prompt(**prompt_input).to_messages())

        if isinstance(result, list) and result and hasattr(result[0], "content"):
            return result[0].content.strip()
        elif hasattr(result, "content"):
            return result.content.strip()
        elif isinstance(result, str) and result.strip():
            return result.strip()
        else:
            return "❌ LLM returned an empty or unexpected result."

    except Exception as e:
        return f"❌ Failed to generate proposal. Reason: {str(e)}"


import re
def format_innovation_proposal(raw_text: str) -> str:
    emoji_headers = {
        "Title": "💡", "Introduction": "📚", "Research Objectives": "🎯",
        "Research Questions": "❓", "Methodology": "🧪", "Expected Outcomes": "🚀",
        "Impact": "🌍", "Timeline": "⏳", "Personnel": "👥", "Resources": "🧰", "Conclusion": "🔚"
    }

    lines = raw_text.split("\n")
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        section_match = re.match(r"\*\*(.+?):\*\*", line)
        if section_match:
            title = section_match.group(1)
            emoji = emoji_headers.get(title, "")
            if title == "Title":
                formatted.append(f"# {emoji} Innovation Proposal: {line.replace('**Title:**', '').strip()}")
                formatted.append("---")
            else:
                formatted.append(f"\n## {emoji} {title}")
            continue

        numbered = re.match(r"(\d+)\.\s*(?:\*\*(.*?)\*\*:)?\s*(.+)", line)
        if numbered:
            num, bold, text = numbered.groups()
            emoji_num = {
                "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
                "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"
            }.get(num, f"{num}.")
            if bold:
                formatted.append(f"{emoji_num} **{bold}**: {text}")
            else:
                formatted.append(f"{emoji_num} {text}")
            continue

        formatted.append(f"- {line}")

    return "\n".join(formatted)
def save_proposal_as_markdown(topic, keywords, proposal_text, filename="proposal.md"):
    content = f"# Research Proposal: {topic}\n\n"
    content += "## Extracted Keywords:\n"
    content += "\n".join(f"- {kw}" for kw in keywords)
    content += "\n\n## Proposal:\n"
    content += proposal_text
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename
