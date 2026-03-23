import os
import json
from dotenv import load_dotenv
from google import genai
from utils.vector_store import search_vector_store

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_machine(machine_name: str, logs: str) -> dict:
    prompt = (
        f"You are an expert industrial maintenance engineer.\n"
        f"Analyze the following maintenance logs for {machine_name}.\n\n"
        f"Logs:\n{logs}\n\n"
        f"Return ONLY a valid JSON object with these exact fields:\n"
        f'{{"machine_name": "{machine_name}", '
        f'"risk_score": <integer 0-100>, '
        f'"status": "<OK, Medium, High, or Critical>", '
        f'"pattern_found": "<short description>", '
        f'"predicted_failure": "<timeframe e.g. within 3 days>", '
        f'"recommended_action": "<specific action>", '
        f'"spare_parts": "<comma separated parts needed>"}}\n\n'
        f"Rules:\n"
        f"- risk_score 80-100 = Critical\n"
        f"- risk_score 60-79 = High\n"
        f"- risk_score 40-59 = Medium\n"
        f"- risk_score 0-39 = OK\n"
        f"- Return ONLY the JSON, no extra text"
    )
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def generate_schedule(machines: list) -> list:
    sorted_machines = sorted(machines, key=lambda x: x["risk_score"], reverse=True)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    times = ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"]
    schedule = []
    slot = 0
    for machine in sorted_machines:
        day = days[min(slot // len(times), len(days) - 1)]
        time = times[slot % len(times)]
        duration = "3-4 hours" if machine["status"] == "Critical" else \
                   "2-3 hours" if machine["status"] == "High" else "1-2 hours"
        schedule.append({
            "machine_name": machine["machine_name"],
            "risk_score": machine["risk_score"],
            "status": machine["status"],
            "day": day,
            "time": time,
            "duration": duration,
            "recommended_action": machine["recommended_action"],
            "spare_parts": machine["spare_parts"]
        })
        slot += 1
    return schedule


def query_agent(question: str) -> dict:
    relevant_docs = search_vector_store(question, n_results=5)
    context = "\n\n".join(relevant_docs) if relevant_docs else "No logs available."
    prompt = (
        "You are MaintainIQ, an AI assistant for a manufacturing plant.\n"
        "Answer the technician's question using the maintenance logs below.\n\n"
        f"Logs context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Give a clear, specific, actionable answer with dates and part details."
    )
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return {
        "answer": response.text.strip(),
        "sources_used": len(relevant_docs),
        "context_found": len(context) > 50
    }