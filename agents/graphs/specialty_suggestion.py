"""
Specialty Suggestion Graph (agents/graphs/specialty_suggestion.py)
Uses Groq Llama 3.3 70B to map free-text patient symptoms to hospital specialty categories.
ENFORCES STRICT GUARDRAIL: Output is a filter suggestion ONLY; never a medical diagnosis.
"""

import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SpecialtySuggestionResponse(BaseModel):
    suggestedSpecialty: str = Field(description="Primary suggested medical specialty category e.g. Cardiology, Neurology, Pediatrics")
    secondarySpecialties: List[str] = Field(default_factory=list, description="Additional relevant specialty categories")
    reasoning: str = Field(description="Brief, non-diagnostic explanation of why these hospital departments match the input keywords")
    disclaimer: str = Field(
        default="Suggested based on symptom keywords to help filter nearby hospitals. This is NOT a medical diagnosis.",
        description="Mandatory clinical disclaimer"
    )

def suggest_specialty_groq(symptoms: str) -> Dict[str, Any]:
    """
    Calls Groq Llama 3.3 70B to parse symptom keywords into hospital specialty categories.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    
    if groq_key and not groq_key.startswith("YOUR_"):
        try:
            from langchain_groq import ChatGroq
            from dotenv import load_dotenv
            load_dotenv()

            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=groq_key,
                temperature=0.1
            ).with_structured_output(SpecialtySuggestionResponse)

            prompt = f"""
            You are a hospital department routing assistant. 
            Analyze the following patient symptom description:
            "{symptoms}"

            CRITICAL GUARDRAILS:
            1. DO NOT diagnose the patient. 
            2. Map the symptoms to 1 primary hospital department specialty (e.g. Cardiology, Neurology, Gastroenterology, Orthopedics, Pediatrics, Emergency).
            3. Provide a brief 1-sentence non-diagnostic rationale explaining why this hospital department treats these symptoms.
            """

            result: SpecialtySuggestionResponse = llm.invoke(prompt)
            return result.dict()
        except Exception as e:
            print(f"Groq specialty suggestion error, using fallback: {e}")

    # Deterministic fallback logic
    s_lower = symptoms.lower()
    if any(kw in s_lower for kw in ["chest", "heart", "cardiac", "pulse"]):
        spec = "Cardiology"
    elif any(kw in s_lower for kw in ["brain", "headache", "dizzy", "seizure", "numb"]):
        spec = "Neurology"
    elif any(kw in s_lower for kw in ["stomach", "vomit", "abdomen", "gastric"]):
        spec = "Gastroenterology"
    elif any(kw in s_lower for kw in ["bone", "fracture", "joint", "knee", "back"]):
        spec = "Orthopedics"
    elif any(kw in s_lower for kw in ["child", "baby", "pediatric"]):
        spec = "Pediatrics"
    else:
        spec = "General Medicine"

    return {
        "suggestedSpecialty": spec,
        "secondarySpecialties": ["General Medicine", "Emergency"],
        "reasoning": f"Filtered hospital departments matching keywords in '{symptoms}'.",
        "disclaimer": "Suggested based on symptom keywords to help filter nearby hospitals. This is NOT a medical diagnosis."
    }

if __name__ == "__main__":
    res = suggest_specialty_groq("severe chest pain radiating to left arm")
    import json
    print(json.dumps(res, indent=2))
