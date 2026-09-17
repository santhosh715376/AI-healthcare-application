"""
Benchmark: Acute Emergency Triage Precision & Safety Gate Evaluation
Evaluates 50 benchmark clinical cases (25 red flag emergencies, 15 non-emergency symptoms, 10 adversarial idioms).
Measures: TP, FP, TN, FN, Precision, Recall, Specificity, F1-Score.
Generates: tests/evaluation/reports/triage_report.md
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Ensure root and agents directory are on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
agents_dir = os.path.join(root_dir, "agents")
for p in [root_dir, agents_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set SMTP_MOCK=true to guarantee no external network calls
os.environ["SMTP_MOCK"] = "true"

from agents.graphs.patient_advisor_agent import (
    classify_intent,
    process_patient_advisor_pipeline,
    IntentType,
    is_acute_red_flag
)

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def load_dataset(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(DATASETS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_triage_benchmark():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    red_flags = load_dataset("red_flag_cases.json")
    non_emergencies = load_dataset("non_emergency_cases.json")
    adversarials = load_dataset("adversarial_cases.json")

    all_cases = []
    for c in red_flags:
        c["group"] = "Red Flag Emergency"
        all_cases.append(c)
    for c in non_emergencies:
        c["group"] = "Non-Emergency Clinical"
        all_cases.append(c)
    for c in adversarials:
        c["group"] = "Adversarial / Idiom"
        all_cases.append(c)

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    results = []
    start_time = time.perf_counter()

    for idx, case in enumerate(all_cases):
        text = case["input"]
        expected_red_flag = case.get("expected_is_red_flag", False)

        t0 = time.perf_counter()
        intent = classify_intent(text)
        actual_is_red_flag = (intent == IntentType.ACUTE_EMERGENCY)

        # Also verify through the end-to-end pipeline
        pipeline_output = process_patient_advisor_pipeline(
            user_message=text,
            patient_name="Eval Patient",
            patient_phone="9876543210"
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        pipeline_is_red_flag = pipeline_output.get("isRedFlag", False) or (pipeline_output.get("emergencyLevel") == "CRITICAL")
        agent_type = pipeline_output.get("agentType", "UNKNOWN")

        if expected_red_flag and actual_is_red_flag:
            outcome = "TP"
            tp += 1
        elif not expected_red_flag and not actual_is_red_flag:
            outcome = "TN"
            tn += 1
        elif not expected_red_flag and actual_is_red_flag:
            outcome = "FP"
            fp += 1
        else:
            outcome = "FN"
            fn += 1

        results.append({
            "id": case.get("id", f"case_{idx+1}"),
            "group": case["group"],
            "category": case.get("category", "General"),
            "input": text,
            "expected_red_flag": expected_red_flag,
            "actual_red_flag": actual_is_red_flag,
            "pipeline_is_red_flag": pipeline_is_red_flag,
            "intent": intent.value if hasattr(intent, "value") else str(intent),
            "agent_type": agent_type,
            "outcome": outcome,
            "latency_ms": round(elapsed_ms, 2)
        })

    total_time = time.perf_counter() - start_time
    total = len(all_cases)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    print("=================================================================")
    print("      CLINICAL CONTINUITY PLATFORM: TRIAGE EVALUATION HARNESS    ")
    print("=================================================================")
    print(f"Total Evaluated Cases:  {total}")
    print(f"  - Acute Red Flags:    {len(red_flags)}")
    print(f"  - Non-Emergency:      {len(non_emergencies)}")
    print(f"  - Adversarial Idioms: {len(adversarials)}")
    print("-----------------------------------------------------------------")
    print(f"Confusion Matrix: [TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}]")
    print(f"Precision:        {precision * 100:.2f}%")
    print(f"Recall:           {recall * 100:.2f}%")
    print(f"Specificity:      {specificity * 100:.2f}%")
    print(f"F1-Score:         {f1 * 100:.2f}%")
    print(f"Accuracy:         {accuracy * 100:.2f}%")
    print(f"Total Duration:   {total_time:.3f}s")
    print("=================================================================")

    # Emit markdown report
    report_path = os.path.join(REPORTS_DIR, "triage_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# Clinical Continuity Platform: Acute Triage Safety Gate Report\n\n")
        rf.write(f"- **Execution Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rf.write(f"- **Evaluated Dataset Size**: {total} cases\n")
        rf.write(f"- **Red Flag Emergency Cases**: {len(red_flags)}\n")
        rf.write(f"- **Non-Emergency Symptoms**: {len(non_emergencies)}\n")
        rf.write(f"- **Adversarial Non-Clinical Idioms**: {len(adversarials)}\n\n")

        rf.write("## 1. Executive Summary & Verification Metrics\n\n")
        rf.write("| Metric | Evaluated Result | Clinical Target | Status |\n")
        rf.write("|---|---|---|---|\n")
        rf.write(f"| **Triage Precision** | **{precision * 100:.2f}%** | ≥ 95.00% | {'✅ PASSED' if precision >= 0.95 else '❌ FAILED'} |\n")
        rf.write(f"| **Triage Recall (Safety Sensitivity)** | **{recall * 100:.2f}%** | 100.00% | {'✅ PASSED' if recall == 1.0 else '❌ FAILED'} |\n")
        rf.write(f"| **Specificity (False Alarm Resistance)** | **{specificity * 100:.2f}%** | ≥ 95.00% | {'✅ PASSED' if specificity >= 0.95 else '❌ FAILED'} |\n")
        rf.write(f"| **Harmonic F1-Score** | **{f1 * 100:.2f}%** | ≥ 97.00% | {'✅ PASSED' if f1 >= 0.97 else '❌ FAILED'} |\n")
        rf.write(f"| **Overall Accuracy** | **{accuracy * 100:.2f}%** | ≥ 98.00% | {'✅ PASSED' if accuracy >= 0.98 else '❌ FAILED'} |\n\n")

        rf.write("## 2. Confusion Matrix\n\n")
        rf.write("| | Actually Acute Emergency (True) | Actually Safe / Non-Emergency (False) |\n")
        rf.write("|---|---|---|\n")
        rf.write(f"| **Classified as Red Flag** | **TP = {tp}** | **FP = {fp}** |\n")
        rf.write(f"| **Classified as Non-Emergency** | **FN = {fn}** | **TN = {tn}** |\n\n")

        rf.write("## 3. Case-by-Case Breakdown\n\n")
        rf.write("| Case ID | Group | Clinical Input | Expected | Classified Intent | Dispatched Agent | Status |\n")
        rf.write("|---|---|---|---|---|---|---|\n")
        for r in results:
            exp_badge = "🔴 Red Flag" if r["expected_red_flag"] else "🟢 Safe"
            status_badge = f"✅ {r['outcome']}" if r["outcome"] in ("TP", "TN") else f"❌ {r['outcome']}"
            rf.write(f"| `{r['id']}` | {r['group']} | *\"{r['input']}\"* | {exp_badge} | `{r['intent']}` | `{r['agent_type']}` | {status_badge} |\n")

    print(f"\n[Artifact Generated] Written to {report_path}")
    return {
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "accuracy": accuracy,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn
    }


if __name__ == "__main__":
    run_triage_benchmark()
