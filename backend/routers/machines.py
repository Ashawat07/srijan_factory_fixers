import os
import io
import time
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.ai_agent import analyze_machine, generate_schedule, query_agent
from utils.db import get_connection

router = APIRouter(tags=["Machines"])

def extract_machines_from_logs():
    conn = get_connection()
    logs_rows = conn.execute("SELECT * FROM logs").fetchall()
    conn.close()

    machines_dict = {}

    for row in logs_rows:
        log_text = row["log_text"]
        source = row["source_file"]
        print(f"Processing: {source}, length: {len(log_text)}")

        # Try CSV parsing first
        if source.endswith(".csv"):
            try:
                df = pd.read_csv(io.StringIO(log_text))
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                print(f"CSV columns: {list(df.columns)}")
                print(f"CSV rows: {len(df)}")

                # Find machine name column
                name_col = None
                for col in ["machine_name", "machine", "equipment", "equipment_name"]:
                    if col in df.columns:
                        name_col = col
                        break

                if name_col:
                    for _, r in df.iterrows():
                        name = str(r[name_col]).strip()
                        if name and name != "nan" and len(name) > 2:
                            if name not in machines_dict:
                                machines_dict[name] = []
                            entry = ", ".join([f"{c}: {r[c]}" for c in df.columns])
                            machines_dict[name].append(entry)
                    print(f"Machines found from CSV: {list(machines_dict.keys())}")
                else:
                    print("No machine_name column found in CSV!")
            except Exception as e:
                print(f"CSV parse error: {e}")

        # For text files - look for machine name patterns
        else:
            lines = log_text.split("\n")
            current_machine = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Detect machine name headers like "--- CNC Machine #4 ---"
                if line.startswith("---") and line.endswith("---"):
                    current_machine = line.replace("-", "").strip()
                    if current_machine not in machines_dict:
                        machines_dict[current_machine] = []
                elif current_machine and line:
                    machines_dict[current_machine].append(line)

    return machines_dict


@router.post("/analyze")
def analyze_all_machines():
    machines_dict = extract_machines_from_logs()

    print(f"Total machines to analyze: {len(machines_dict)}")
    print(f"Machine names: {list(machines_dict.keys())}")

    if not machines_dict:
        raise HTTPException(
            status_code=400,
            detail="No machines found in uploaded logs. Make sure your CSV has a 'machine_name' column."
        )

    results = []
    conn = get_connection()

    for machine_name, machine_logs in machines_dict.items():
        log_text = "\n".join(machine_logs[:10])
        try:
            time.sleep(3)
            print(f"Analyzing: {machine_name}")
            analysis = analyze_machine(machine_name, log_text)
            conn.execute("""
                INSERT OR REPLACE INTO machines
                (machine_name, risk_score, status, predicted_failure, recommended_action, spare_parts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis["machine_name"],
                analysis["risk_score"],
                analysis["status"],
                analysis["predicted_failure"],
                analysis["recommended_action"],
                analysis["spare_parts"]
            ))
            conn.commit()
            results.append(analysis)
            print(f"Done: {machine_name} -> risk_score: {analysis['risk_score']}, status: {analysis['status']}")
        except Exception as e:
            print(f"Error analyzing {machine_name}: {e}")
            results.append({"machine_name": machine_name, "error": str(e)})

    conn.close()
    return {
        "status": "success",
        "machines_analyzed": len(results),
        "results": results
    }


@router.get("/machines")
def get_all_machines():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM machines ORDER BY risk_score DESC").fetchall()
    conn.close()
    return {"machines": [dict(row) for row in rows]}


@router.get("/schedule")
def get_schedule():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM machines ORDER BY risk_score DESC").fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="No machines found. Run /analyze first.")
    machines = [dict(row) for row in rows]
    schedule = generate_schedule(machines)
    return {"schedule": schedule}


@router.get("/summary")
def get_summary():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM machines").fetchall()
    conn.close()
    machines = [dict(row) for row in rows]
    critical = sum(1 for m in machines if m["status"] == "Critical")
    high = sum(1 for m in machines if m["status"] == "High")
    ok = sum(1 for m in machines if m["status"] == "OK")
    avg_risk = round(sum(m["risk_score"] for m in machines) / len(machines)) if machines else 0
    return {
        "total_machines": len(machines),
        "critical": critical,
        "high": high,
        "ok": ok,
        "avg_risk_score": avg_risk
    }


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query_maintenance(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = query_agent(request.question)
    return result