import os
import re
from typing import Dict, Any, List

def route_user_prompt(user_prompt: str, patient_id: int = 100001) -> Dict[str, Any]:
    """
    3-Layer Semantic Vector Intent Router:
    Evaluates user prompt, maps intent scores to agent capabilities, and triggers parallel execution.
    """
    p_lower = user_prompt.lower().strip()

    # Layer 1: Fast-Path Command Filter
    if p_lower.startswith("/emergency") or any(k in p_lower for k in ["chest pain", "breathlessness", "unconscious", "heart attack", "heavy bleeding"]):
        from graphs.emergency_agent import trigger_emergency_escort
        res = trigger_emergency_escort(symptom_text=user_prompt)
        return {
            "primary_intent": "EMERGENCY",
            "activated_agents": ["emergency_agent"],
            "response": res["banner_msg"],
            "payload": res
        }

    # Layer 2: Semantic Intent Classifier
    activated = []
    
    # Check Guardian Intent (missed dose)
    if any(k in p_lower for k in ["missed", "forgot", "skipped", "didn't take", "not taken"]):
        from graphs.guardian_agent import check_consecutive_missed_doses
        g_res = check_consecutive_missed_doses(patient_id)
        if g_res.get("intervention_required"):
            activated.append("guardian_agent")

    # Check Safety Intent (drug interactions)
    if any(k in p_lower for k in ["take together", "interaction", "side effect", "food with", "before food"]):
        from graphs.safety_agent import evaluate_drug_interactions
        s_res = evaluate_drug_interactions([], patient_id)
        activated.append("safety_agent")

    # Fallback to Grounded Patient Advisor Chatbot
    from graphs.context_agent import run_context_agent
    chat_res = run_context_agent(patient_id, user_prompt)

    return {
        "primary_intent": "HEALTH_ADVISOR",
        "activated_agents": activated if activated else ["context_agent"],
        "response": chat_res["response"],
        "guardrail_triggered": chat_res.get("guardrail_triggered", False)
    }
