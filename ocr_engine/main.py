import os
import json
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Gemini 2.0 Flash OCR Engine")

# System prompt enforcing strict Healthcare guardrails
OCR_SYSTEM_PROMPT = """
You are an expert medical OCR assistant specializing in handwritten and printed doctor prescriptions.
Examine the uploaded prescription image carefully and extract structured JSON matching the following schema.

CRITICAL MEDICAL GUARDRAILS:
1. ONLY extract explicitly stated diagnoses into 'recordedDiagnosis'. NEVER infer or guess an unstated medical condition. If no diagnosis is written, leave 'recordedDiagnosis' as empty string "".
2. Extract all medications, including medicine name, dosage, frequency (e.g. 1-0-1, TDS, BD), duration, and food relation (Before Food / After Food).
3. Extract header details (Doctor Name, Hospital/Clinic Name, OPD Contact, Date) if visible.
4. Extract tail details (Advice, Follow Up date) if visible.

OUTPUT FORMAT: Return raw valid JSON ONLY adhering to this exact structure:
{
  "id": "rx-ocr-1001",
  "patientId": "pat-1001",
  "source": "patient_ocr",
  "header": {
    "doctorName": "string",
    "hospitalName": "string",
    "opdContact": "string",
    "date": "string"
  },
  "body": {
    "recordedDiagnosis": "string",
    "medications": [
      {
        "name": "string",
        "dosage": "string",
        "frequency": "string",
        "duration": "string",
        "foodRelation": "string"
      }
    ]
  },
  "tail": {
    "advice": "string",
    "followUpDate": "string"
  }
}
"""

@app.post("/extract_text")
async def extract_text(image: UploadFile = File(...)):
    """
    Accepts an image file, uses Gemini 2.0 Flash to parse handwritten/printed prescription,
    and returns 3-Section Header-Body-Tail structured JSON.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY environment variable not set. Please export GEMINI_API_KEY."
        )

    try:
        # Read image bytes
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))

        # Initialize Google GenAI client
        client = genai.Client(api_key=api_key)

        # Call Gemini 2.0 Flash Vision model
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[pil_image, OCR_SYSTEM_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        structured_json = json.loads(response.text)
        return structured_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini OCR Parsing Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
