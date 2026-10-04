import os, json
from dotenv import load_dotenv
from google import genai
from ddgs import DDGS

load_dotenv()
API_KEY=os.getenv("GEMINI_API_KEY")
MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")

def ask_gemini(prompt: str) -> str:
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")
    client=genai.Client(api_key=API_KEY)
    response=client.models.generate_content(model=MODEL, contents=prompt)
    return response.text or ""

def make_plan(topic: str, depth: str) -> list[str]:
    count={"Quick":3,"Standard":5,"Deep":7}[depth]
    prompt=f"""You are a research-planning agent. Break this research question into exactly {count} focused, non-overlapping research tasks.
Return ONLY a JSON array of short strings, with no markdown.
Research question: {topic}"""
    raw=ask_gemini(prompt).strip()
    raw=raw.removeprefix("```json").removesuffix("```").strip()
    plan=json.loads(raw)
    if not isinstance(plan,list) or not all(isinstance(x,str) for x in plan):
        raise ValueError("Planner returned an invalid task list.")
    return plan

def search_web(query: str, limit: int=4) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results=list(ddgs.text(query, max_results=limit))
        return [{"title":r.get("title","Untitled"),"url":r.get("href",""),"snippet":r.get("body","")} for r in results]
    except Exception:
        return []

def research_task(task: str, topic: str, depth: str) -> tuple[str,list[dict]]:
    limit={"Quick":2,"Standard":4,"Deep":6}[depth]
    sources=search_web(task,limit)
    evidence="\n\n".join(f"Title: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}" for s in sources)
    prompt=f"""You are a careful research agent. Research task: {task}
Overall question: {topic}
Use the search snippets below as leads, not as unquestionable facts. Clearly distinguish supported findings from uncertainty. Do not invent citations or claim you read pages beyond the snippets.
Search results:
{evidence if evidence else "No web results were available. Use general knowledge cautiously and disclose the limitation."}
Write concise findings and include source URLs inline where relevant."""
    return ask_gemini(prompt),sources

def analyze_and_report(topic: str, findings: list[str]) -> str:
    prompt=f"""You are the analysis and report-writing agent. Synthesize the research notes into a useful, balanced report answering: {topic}
Use Markdown with sections: Executive Summary, Key Findings, Analysis, Limitations, Conclusion.
Do not invent facts, statistics, or sources. Mention conflicting or weak evidence and note when the research notes do not establish a claim.
Research notes:
{chr(10).join(f'--- Task {i+1} ---\n{x}' for i,x in enumerate(findings))}"""
    return ask_gemini(prompt)

def run_research(topic: str, depth: str="Standard") -> dict:
    plan=make_plan(topic,depth)
    findings=[]
    all_sources=[]
    for task in plan:
        note,sources=research_task(task,topic,depth)
        findings.append(note)
        all_sources.extend(sources)
    report=analyze_and_report(topic,findings)
    seen=set()
    unique=[]
    for s in all_sources:
        if s["url"] and s["url"] not in seen:
            seen.add(s["url"]); unique.append(s)
    return {"plan":plan,"findings":findings,"sources":unique,"report":report}
