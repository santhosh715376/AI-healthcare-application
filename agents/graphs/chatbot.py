"""
Health Chatbot Graph (agents/graphs/chatbot.py)
Simple stateless Groq Llama 3.3 70B chatbot.
No RAG, no patient records — pure conversational health information assistant.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))# ─── System Prompts ────────────────────────────────────────────────────────────
PATIENT_SYSTEM_PROMPT = """You are a specialized consumer healthcare information assistant.
Output rules:
- STRICT DOMAIN SCOPE: Answer only health, medication, and hospital-related questions. Reject non-medical queries in one line.
- Plain sentences by default. No headers, no bold, no emojis.
- Max 120 words unless detail requested.
- NEVER DIAGNOSE. Recommend a professional if symptoms suggest urgency.
- No filler openers ("Great question", "Sure"). Start directly with the answer."""

DOCTOR_SYSTEM_PROMPT = """You are an advanced Clinical Research & Decision-Support AI Assistant for verified physicians.
Capabilities & Directives:
- CLINICAL RESEARCH MODE ENABLED: Assist doctors with disease research, differential diagnosis guidance, drug-drug interaction analysis, mechanism of action, pharmacology, and treatment protocols.
- INGEST PATIENT CONTEXT: Use the provided patient health context to evaluate specific patient cases, drug contraindications, and therapeutic options.
- PROFUSE CLINICAL DETAIL: Provide thorough, professional medical terminology, standard dosages, and evidence-based clinical reasoning.
- Output formatting: Use markdown headers, bullet points, and tables where clinical clarity requires it."""


# ─── In-Memory Session Store ──────────────────────────────────────────────────
# { sessionId: [{"role": "user"|"assistant", "content": "..."}, ...] }
CHAT_SESSIONS: Dict[str, List[Dict[str, str]]] = {}

MAX_HISTORY = 20  # keep last 20 turns per session


def chat_with_groq(session_id: str, user_message: str, patient_id: str = "pat-1001", role: str = "patient") -> str:
    """
    Sends user_message to Groq Llama 3.3 70B with session history and Timeline Context Agent injection.
    Supports role='doctor' (clinical research mode with RAG) vs role='patient' (strictly guardrailed consumer mode).
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key or groq_key.startswith("YOUR_"):
        raise ValueError("GROQ_API_KEY is missing or not configured in .env")

    from groq import Groq
    from graphs.context_agent import build_patient_health_context
    from graphs.specialty_suggestion import suggest_specialty_groq

    # Fetch Timeline Context Agent Enriched Block
    context_data = build_patient_health_context(patient_id)
    timeline_context = context_data.get("systemPromptContext", "")

    if role.lower() == "doctor":
        base_prompt = DOCTOR_SYSTEM_PROMPT
        specialty_context = ""
    else:
        base_prompt = PATIENT_SYSTEM_PROMPT
        # Run Specialty Router Agent for patient queries
        specialty_context = ""
        try:
            specialty_info = suggest_specialty_groq(user_message)
            if specialty_info.get("suggestedSpecialty") and specialty_info["suggestedSpecialty"] != "General Medicine":
                specialty_context = f"""
[SPECIALTY ROUTER AGENT RECOMMENDATION]
Symptom query detected. Direct patient to the suitable hospital specialty department:
- Primary Hospital Department: {specialty_info['suggestedSpecialty']}
- Secondary Departments: {", ".join(specialty_info.get('secondarySpecialties', []))}
- Rationale: {specialty_info.get('reasoning', '')}

CRITICAL DIRECTIVE: You MUST explicitly advise the user to: "Consult a doctor before taking any serious action."
"""
        except Exception as e:
            print(f"Error running sub-agent specialty suggestion: {e}")

    # Combine base system prompt, timeline context, and specialty agent routing info
    effective_system_prompt = f"{base_prompt}\n\n{timeline_context}\n\n{specialty_context}"

    # Initialize session if new
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[session_id] = []

    history = CHAT_SESSIONS[session_id]

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Trim to last MAX_HISTORY turns
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        CHAT_SESSIONS[session_id] = history

    # Build messages array with effective system prompt
    messages = [{"role": "system", "content": effective_system_prompt}] + history

    client = Groq(api_key=groq_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3 if role.lower() == "doctor" else 0.4,
        max_tokens=800 if role.lower() == "doctor" else 400,
    )

    reply = response.choices[0].message.content.strip()

    # Store assistant reply in history
    history.append({"role": "assistant", "content": reply})

    print(f"[ChatBot ({role})] session={session_id} | user: {user_message[:60]}... | reply: {reply[:80]}...")
    return reply


def clear_session(session_id: str) -> None:
    """Clears conversation history for a session."""
    if session_id in CHAT_SESSIONS:
        del CHAT_SESSIONS[session_id]
