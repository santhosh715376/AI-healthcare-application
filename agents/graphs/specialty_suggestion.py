import os
import json
import requests
from typing import Dict, Any

STATIC_HIGH_URGENCY_BANNER = "Call 108 or your nearest ER directly if this is severe."

def classify_specialty_and_urgency(symptom_text: str) -> Dict[str, Any]:
    """
    Uses Groq llama-3.1-8b-instant to classify symptom text into:
    - specialty (e.g. Cardiology, Trauma, Pediatrics, Orthopedics, General Medicine)
    - urgency ("HIGH" | "MEDIUM" | "LOW")
    - reasoning (1 sentence explanation)
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("[SpecialtyClassifier] GROQ_API_KEY missing, using deterministic fallback.")
        symptom_lower = symptom_text.lower()
        if any(k in symptom_lower for k in ["chest", "heart", "cardiac", "stroke", "numbness"]):
            return {
                "specialty": "Cardiology",
                "urgency": "HIGH",
                "reasoning": "Symptoms of potential cardiac or vascular emergency require immediate cardiology triage."
            }
        elif any(k in symptom_lower for k in ["fracture", "bone", "joint", "sprain", "dislocation"]):
            return {
                "specialty": "Orthopedics",
                "urgency": "MEDIUM",
                "reasoning": "Musculoskeletal injury requires orthopedic evaluation."
            }
        else:
            return {
                "specialty": "General Medicine",
                "urgency": "LOW",
                "reasoning": "General clinical evaluation recommended."
            }

    prompt = f"""You are a clinical triage classifier. Analyze the user's symptom description:
"{symptom_text}"

Respond strictly in JSON with 3 keys:
1. "specialty": Most relevant medical specialty (e.g. Cardiology, Trauma, Pediatrics, Orthopedics, General Medicine, Neurology).
2. "urgency": "HIGH" (life-threatening/severe), "MEDIUM" (urgent care needed), or "LOW" (routine/non-urgent).
3. "reasoning": 1 sentence explaining the clinical classification.

Output JSON ONLY:"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "specialty": parsed.get("specialty", "General Medicine"),
            "urgency": parsed.get("urgency", "MEDIUM").upper(),
            "reasoning": parsed.get("reasoning", "Clinical triage evaluation completed.")
        }
    except Exception as e:
        print(f"[SpecialtyClassifier] Groq API call error: {e}")
        return {
            "specialty": "General Medicine",
            "urgency": "MEDIUM",
            "reasoning": "General clinical triage evaluation fallback."
        }

# Alias for server compatibility
suggest_specialty_groq = classify_specialty_and_urgency
