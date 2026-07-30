# Walkthrough: Health AI Chatbot (Phase 1 — Standalone MVP)

The Health AI Chatbot is fully implemented and live on **[http://localhost:5173](http://localhost:5173)**!

---

## 1. What Was Built

### A. Backend (`agents/graphs/chatbot.py` & `agents/server.py`)
- Created `chat_with_groq(session_id, user_message)` using **Groq Llama 3.3 70B** (`llama-3.3-70b-versatile`).
- Embedded the exact system prompt rules:
  - Plain sentences by default (no headers, no bold, no emojis).
  - Use numbered lists ONLY for 3+ sequential steps.
  - Use short tables ONLY when comparing 2+ options.
  - Max 120 words unless detail requested.
  - Never diagnose; one-line professional recommendation on urgency.
  - No filler openers ("Great question", "Sure, here's...").
- Exposed `POST /api/chat/message` and `POST /api/chat/clear` endpoints.

### B. Frontend (`ChatPage.jsx`, `ChatBubble.jsx`, `CapturePage.jsx`, `index.css`)
- **State 1 — Landing Screen**: Black screen centered vertically with `"Where should we begin?"` and dark pill input bar.
- **State 2 — Chat Thread View**: Right-aligned dark user message pills and left-aligned plain text AI answers with faint reasoning tag (`"Devised straightforward explanation for query"`).
- Added **`💬 Health AI Chatbot`** as Tab 4 in the top navigation bar.

---

## 2. Test in Your Browser Now

Refresh **[http://localhost:5173](http://localhost:5173)** in your browser:
1. Click the **"💬 Health AI Chatbot"** tab in the navbar.
2. Observe the landing screen: **"Where should we begin?"** with a central pill search bar.
3. Type: `"What is paracetamol?"` and press Enter.
   - User message appears as a right-aligned dark pill.
   - AI responds in plain, clean sentences without headers, bold text, or emojis (~78 words).
4. Type: `"Compare ibuprofen vs paracetamol for fever"` and press Enter.
   - AI formats the output as a clean comparative markdown table.
5. Type: `"I have severe chest pain and breathlessness"` and press Enter.
   - AI gives a single-line urgent warning to seek professional care immediately.
