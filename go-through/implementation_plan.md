# Implementation Plan: Server Restart Fix & Web Page Bottom-Middle OCR Button

This document outlines why the server output did not change previously and details the layout position fix for the OCR parse button.

---

## 1. Diagnostic Discovery: Why the server returned 1 medication previously

> [!IMPORTANT]
> **Root Cause:**
> The FastAPI backend server (`agents/server.py`) running in task `task-778` was launched *before* we updated `prescription_parser.py`.
> Because `uvicorn.run(app, ...)` was running without auto-reload, **the server held the old 1-medication fallback code in memory**.
> 
> **Solution:** 
> Kill background task `task-778` and restart `python agents/server.py` so the server loads the updated `gemini-2.0-flash` vision parser into memory!

---

## 2. Web Page Bottom-Middle OCR Button Position Fix

> [!IMPORTANT]
> **Position Fix:**
> Currently, the **"⚡ Parse Image with Gemini OCR"** button is rendered inside the left pane.
> We will move the button to the **web page bottom middle** container (`mic-floating-bar`), identical to the voice Push-to-Speak mic button!

---

## Proposed Code Changes

### Backend Server (`agents/server.py`)
- Restart the FastAPI server to pick up `gemini-2.0-flash`.

### Frontend (`frontend/src/` & `health_care/src/`)
- Update `CapturePage.jsx` to render the OCR floating button at the **web page bottom-middle** (`position: absolute; bottom: 24px; left: 50%`).

---

## Verification Plan

### Manual Verification
1. Restart `python agents/server.py`.
2. Refresh `http://localhost:5173`.
3. Go to Tab 2 (OCR Prescription Upload).
4. Verify the **"⚡ Parse Image with Gemini OCR"** button is positioned at the **web page bottom-middle**.
5. Upload `ocr_data/img/img/img 4.jpg` and click the button.
6. Verify right pane extracts **all 4 medications** (`Syp Calpol`, `Syp Delcon`, `Syp Levolin`, `Syp Meftal-P`), `Dr. Nithin Narayanan`, and `URTI`.
