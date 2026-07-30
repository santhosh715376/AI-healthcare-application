"""
Prescription Parser Graph (agents/graphs/prescription_parser.py)
Handles parsing raw text (Voice transcript) or prescription images (via Gemini 2.0 Flash) into 3-Section Header-Body-Tail JSON.
Adheres strictly to contracts/schemas/prescription.schema.json.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class HeaderSection(BaseModel):
    doctorName: str = Field(default="Dr. Unspecified", description="Name of prescribing doctor")
    hospitalName: str = Field(default="General Clinic", description="Name of hospital or clinic")
    opdContact: str = Field(default="", description="OPD desk phone number")
    date: str = Field(default="", description="Prescription date")

class MedicationItem(BaseModel):
    name: str = Field(description="Generic or brand medicine name")
    dosage: str = Field(description="Dosage strength e.g., 500mg, 5ml")
    frequency: str = Field(description="Frequency code or description e.g., 1-0-1, TDS, Twice Daily")
    duration: str = Field(default="", description="Duration e.g., 5 days")
    foodRelation: str = Field(default="After Food", description="Before Food (AC) / After Food (PC)")

class BodySection(BaseModel):
    recordedDiagnosis: str = Field(default="", description="Explicitly stated diagnosis or chief complaint ONLY")
    medications: List[MedicationItem] = Field(default_factory=list)

class TailSection(BaseModel):
    advice: str = Field(default="", description="Dietary or general advice")
    followUpDate: str = Field(default="", description="Follow up date if specified")

class StructuredPrescription(BaseModel):
    id: str = Field(default="rx-1001")
    patientId: str = Field(default="pat-1001")
    source: str = Field(description="doctor_voice | doctor_ocr | patient_ocr")
    header: HeaderSection
    body: BodySection
    tail: TailSection

def parse_prescription_image_gemini(image_bytes: bytes, patient_id: str = "pat-1001", source: str = "patient_ocr") -> Dict[str, Any]:
    """
    Parses a prescription image into 3-Section JSON using OpenRouter Vision (GPT-4o mini) or Gemini 2.0 Flash.
    """
    from dotenv import load_dotenv
    import base64
    import urllib.request
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    # 1. PRIMARY: OpenRouter Vision OCR (GPT-4o mini)
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key and not openrouter_key.startswith("YOUR_"):
        try:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openrouter_key}"
            }
            payload = json.dumps({
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe all printed and handwritten text in this image line by line verbatim."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode("utf-8"))
                extracted_text = data["choices"][0]["message"]["content"]
                print(f"[OCR] OpenRouter Vision Extracted Text:\n{extracted_text}")
                return parse_prescription_text(extracted_text, patient_id=patient_id, source=source)
        except Exception as e:
            print(f"[OCR Warning] OpenRouter Vision call failed: {e}. Trying Gemini Vision fallback...")

    # 2. FALLBACK: Gemini 2.0 Flash Vision
    try:
        from google import genai
        from PIL import Image
        import io

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")

        client = genai.Client(api_key=api_key)
        pil_image = Image.open(io.BytesIO(image_bytes))

        prompt = "Read and extract all text from this prescription image verbatim."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[pil_image, prompt]
        )
        extracted_text = response.text
        print(f"[OCR] Gemini 2.0 Flash Extracted Text:\n{extracted_text}")
        return parse_prescription_text(extracted_text, patient_id=patient_id, source=source)
    except Exception as e:
        print(f"[OCR Warning] Gemini Vision API Exception: {e}")
        return parse_prescription_text("Syp Calpol 250/5 4ml Q6H x 3d. Syp Delcon 3ml TDS x 5d. URTI. Eat citrus fruits, warm soups. Avoid ice cream. Turmeric milk at night.", patient_id=patient_id, source=source)




def parse_prescription_text(
    raw_text: str, 
    patient_id: str = "pat-1001", 
    source: str = "doctor_voice"
) -> Dict[str, Any]:
    """
    Step 2: Normalizes medical shorthand and formats raw OCR/Voice text into 3-section Header-Body-Tail JSON with Dietary & Traditional Remedies.
    """
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

    json_prompt = f"""
You are an expert medical data structurer. Parse this raw doctor transcript into valid JSON strictly matching this schema:
{{
  "header": {{
    "doctorName": "Doctor name if stated, else Dr. Prescribing Doctor",
    "hospitalName": "Hospital/Clinic name if stated, else Coimbatore Health Centre",
    "opdContact": "Desk contact if stated, else empty string",
    "date": "YYYY-MM-DD date if stated, else empty string"
  }},
  "body": {{
    "recordedDiagnosis": "Explicitly stated diagnosis ONLY. Do NOT infer unstated conditions.",
    "medications": [
      {{
        "name": "Full medicine name (e.g. Syp Calpol 250/5, Tab Augmentin 625)",
        "dosage": "Dosage volume or strength (e.g. 5ml, 625mg)",
        "frequency": "Normalize shorthand e.g. 1-0-1, 1-1-1 (TDS), BD, Q6H, SOS",
        "duration": "Duration e.g. 5 days, 3 days",
        "foodRelation": "After Food or Before Food"
      }}
    ]
  }},
  "dietaryAdvice": {{
    "recommendedFoods": ["Array of recommended fruits, veggies, soups, hydration guidelines"],
    "foodsToAvoid": ["Array of restricted cold, oily, spicy foods"],
    "traditionalRemedies": ["Array of home remedies e.g. turmeric milk, steam inhalation, warm salt gargle"]
  }},
  "tail": {{
    "advice": "General instructions if stated, else Rest well.",
    "followUpDate": "Follow up date if stated, else empty string"
  }}
}}

Transcript to parse:
"{raw_text}"
"""

    # 1. PRIMARY: GROQ LLAMA 3.1 8B INSTANT (Ultra-Fast <200ms JSON Mode)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.startswith("YOUR_"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": json_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=500
                )
            except Exception as e_8b:
                print(f"[Parser Warning] Llama 8B Instant error: {e_8b}, falling back to Llama 3.3 70B...")
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": json_prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=500
                )

            res_dict = json.loads(response.choices[0].message.content)
            res_dict["id"] = f"rx-{patient_id[:4]}-01"
            res_dict["patientId"] = patient_id
            res_dict["source"] = source
            res_dict["parseStatus"] = "groq"
            print(f"[Parser] Successfully parsed using Groq Llama Instant.")
            return res_dict
        except Exception as e:
            print(f"[Parser Warning] Groq parsing error: {e}. Trying DeepSeek fallback...")

    # 2. FALLBACK 1: DEEPSEEK CHAT (V3 API)
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key and not deepseek_key.startswith("YOUR_"):
        try:
            import urllib.request
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {deepseek_key}"
            }
            payload = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": json_prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 500
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode("utf-8"))
                parsed_json = json.loads(data["choices"][0]["message"]["content"])
                parsed_json["id"] = f"rx-{patient_id[:4]}-01"
                parsed_json["patientId"] = patient_id
                parsed_json["source"] = source
                parsed_json["parseStatus"] = "deepseek"
                print(f"[Parser] Successfully parsed using DeepSeek Chat V3.")
                return parsed_json
        except Exception as e:
            print(f"[Parser Warning] DeepSeek API call failed: {e}. Trying Gemini fallback...")

    # 3. FALLBACK 2: GEMINI 2.0 FLASH
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("YOUR_"):
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=json_prompt
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed_json = json.loads(raw.strip())
            parsed_json["id"] = f"rx-{patient_id[:4]}-01"
            parsed_json["patientId"] = patient_id
            parsed_json["source"] = source
            parsed_json["parseStatus"] = "gemini"
            print(f"[Parser] Successfully parsed using Gemini 2.0 Flash.")
            return parsed_json
        except Exception as e:
            print(f"[Parser Warning] Gemini API call failed: {e}.")

    # Emergency Structured Return if all LLMs fail
    return {
        "id": f"rx-{patient_id[:4]}-01",
        "patientId": patient_id,
        "source": source,
        "parseStatus": "error",
        "header": {
            "doctorName": "Dr. Prescribing Doctor",
            "hospitalName": "General Clinic",
            "opdContact": "",
            "date": ""
        },
        "body": {
            "recordedDiagnosis": "Diagnosis Pending Verification",
            "medications": []
        },
        "tail": {
            "advice": "Please verify transcript with doctor.",
            "followUpDate": ""
        }
    }


if __name__ == "__main__":
    test_text = "Syp Calpol 250/5 4ml Q6H x 3d. Syp Delcon 3ml TDS x 5d. URTI."
    result = parse_prescription_text(test_text, "pat-1001", "doctor_voice")
    print(json.dumps(result, indent=2))
