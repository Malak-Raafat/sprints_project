import requests # type: ignore 
import xml.etree.ElementTree as ET 
from agents.message_bus import MessageBus  # type: ignore 

bus = MessageBus()
def fetch_arxiv_papers(topic="artificial intelligence", max_results=5):
    url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results={max_results}"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip()
        summary = entry.find("atom:summary", ns).text.strip()
        published = entry.find("atom:published", ns).text
        link = entry.find("atom:link", ns).attrib["href"]

        papers.append({
            "title": title,
            "summary": summary,
            "published": published,
            "link": link
        })
    bus.publish("papers", papers)  # ✅ Publish to message bus

    return papers





