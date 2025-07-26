# agents/analysis_agent.py
from collections import Counter
import re
from agents.message_bus import bus  # type: ignore 

def analyze_papers(papers):
    all_words = []

    for paper in papers:
        text = paper["title"] + " " + paper["summary"]
        words = re.findall(r"\b[a-zA-Z]{5,}\b", text.lower())
        all_words.extend(words)

    keyword_counts = Counter(all_words)
    return keyword_counts.most_common(5)

def analyze_from_bus():
    papers = bus.consume("papers")  
    if not papers:
        return []

    keywords = analyze_papers(papers)
    bus.publish("keywords", keywords)  
    return keywords
