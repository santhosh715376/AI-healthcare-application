import React, { useState, useRef, useEffect } from 'react';
import ChatBubble from '../components/ChatBubble.jsx';

export default function ChatPage({ currentUser }) {
  const username = currentUser?.name || 'Santhosh';

  const initialWelcomeMsg = {
    role: 'assistant',
    agentType: 'WELCOME_BANNER',
    content: `Hi ${username}, how's your health today?

/specialty      – Organ & sector hospital discovery
/report_reader  – Explains lab report values in plain language
/comfort        – Disease diet & comfort guide
/triage         – Symptom likelihood ranking
/emergency      – 24/7 ER assistance

Type a command, or just ask your question.`
  };

  const [messages, setMessages] = useState([initialWelcomeMsg]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pdfContext, setPdfContext] = useState(null);
  const [pdfFileName, setPdfFileName] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handlePdfUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPdfFileName(file.name);
      const reader = new FileReader();
      
      if (file.type.startsWith('image/')) {
        reader.onload = (event) => {
          setPdfContext(`[IMAGE ATTACHMENT: ${file.name}] Attached prescription/diagnostic photo.`);
        };
        reader.readAsDataURL(file);
      } else {
        reader.onload = (event) => {
          const text = event.target.result;
          setPdfContext(text.substring(0, 3000));
        };
        reader.readAsText(file);
      }
    }
  };

  const handleSend = async (overrideText = null) => {
    const textToSend = overrideText || input.trim();
    if (!textToSend || loading) return;

    if (!overrideText) setInput('');

    // Append user message
    setMessages((prev) => [...prev, { role: 'user', content: textToSend }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat/patient-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          patientName: username,
          patientPhone: currentUser?.phone || '9876543210',
          pdfContext: pdfContext,
          lat: 11.0168,
          lng: 76.9558
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.replyText || 'Processed by Patient Assistant Agent.',
          dataPayload: data
        }
      ]);
    } catch (err) {
      console.error('Patient Advisor Chat Error:', err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Connection error. Please ensure the FastAPI server is online.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessages([{
      role: 'assistant',
      agentType: 'WELCOME_BANNER',
      content: `Hi ${username}, how's your health today?\n\n/specialty  – Organ & sector hospital discovery\n/comfort    – Disease diet & comfort guide\n/triage     – Symptom likelihood ranking\n/emergency  – 24/7 ER assistance\n\nType a command, or just ask your question.`
    }]);
    setPdfContext(null);
    setPdfFileName(null);
  };

  return (
    <div style={{
      height: 'calc(100vh - 90px)',
      backgroundColor: '#0d0d0d',
      color: '#ececec',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Top Header Bar */}
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        padding: '12px 24px',
        borderBottom: '1px solid #262626',
        backgroundColor: '#0d0d0d'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontWeight: 600, fontSize: '0.95rem', color: '#ffffff' }}>Health Assistant Chat</span>
          <span style={{ fontSize: '0.75rem', backgroundColor: '#172554', color: '#60a5fa', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>
            Groq Llama 3.3 70B
          </span>
        </div>
        <button
          onClick={handleClear}
          style={{
            backgroundColor: '#171717',
            color: '#a3a3a3',
            border: '1px solid #262626',
            borderRadius: '8px',
            padding: '6px 14px',
            fontSize: '0.8rem',
            cursor: 'pointer',
            fontWeight: 500,
            transition: 'all 0.2s ease'
          }}
        >
          ➕ New Chat
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 16%',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <ChatBubble role={msg.role} content={msg.content} />

            {/* Hospital Recommendation Cards inside Chat */}
            {msg.dataPayload && msg.dataPayload.hospitals && (
              <div style={{ marginTop: '12px', marginLeft: '40px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#60a5fa' }}>
                  🏥 Recommended Specialized Sector Hospitals in Coimbatore District:
                </div>
                {msg.dataPayload.hospitals.map((h) => (
                  <div key={h.id} style={{
                    backgroundColor: '#171717',
                    border: '1px solid #262626',
                    borderRadius: '12px',
                    padding: '14px',
                    color: '#ffffff'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.9rem' }}>
                      <span>#{h.rank} {h.name}</span>
                      <span style={{ color: '#34d399', fontSize: '0.78rem' }}>{h.distanceKm} km away</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#fbbf24', marginTop: '4px' }}>
                      🏆 {h.bestSector}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#a3a3a3', marginTop: '2px' }}>
                      🏥 {h.beds} Beds • {h.category}
                    </div>
                    <a
                      href={h.googleMapsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-block',
                        marginTop: '10px',
                        backgroundColor: '#2563eb',
                        color: '#ffffff',
                        padding: '6px 14px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        textDecoration: 'none'
                      }}
                    >
                      🧭 Get Google Maps Directions
                    </a>
                  </div>
                ))}
              </div>
            )}

            {/* ER Emergency Hospital Cards */}
            {msg.dataPayload && msg.dataPayload.erHospitals && (
              <div style={{ marginTop: '12px', marginLeft: '40px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f87171' }}>
                  🚨 Top 24/7 ER Emergency Hospitals Nearby:
                </div>
                {msg.dataPayload.erHospitals.map((h) => (
                  <div key={h.id} style={{
                    backgroundColor: '#450a0a',
                    border: '1px solid #991b1b',
                    borderRadius: '12px',
                    padding: '14px',
                    color: '#ffffff'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.9rem' }}>
                      <span>#{h.rank} {h.name}</span>
                      <span style={{ color: '#fca5a5', fontSize: '0.78rem' }}>{h.distanceKm} km away</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#fcd34d', marginTop: '4px' }}>
                      ⚡ {h.emergencySpecialty24x7}
                    </div>
                    <a
                      href={h.googleMapsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-block',
                        marginTop: '10px',
                        backgroundColor: '#dc2626',
                        color: '#ffffff',
                        padding: '6px 14px',
                        borderRadius: '8px',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        textDecoration: 'none'
                      }}
                    >
                      🚨 Navigate to 24/7 ER Emergency Room
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', color: '#a3a3a3', fontSize: '0.85rem', marginLeft: '40px' }}>
            <span style={{ animation: 'spin 1s linear infinite' }}>⚙️</span> Processing request...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Transient PDF Attachment Banner */}
      {pdfFileName && (
        <div style={{
          backgroundColor: '#171717',
          borderTop: '1px solid #262626',
          padding: '8px 16%',
          fontSize: '0.8rem',
          color: '#60a5fa',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center'
        }}>
          <span>📄 Attached Transient PDF: <strong>{pdfFileName}</strong> (In-Memory Session Only)</span>
          <button
            onClick={() => { setPdfContext(null); setPdfFileName(null); }}
            style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontWeight: 600 }}
          >
            ✕ Remove
          </button>
        </div>
      )}

      {/* Hidden File Input for PDF Attachment */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf,application/pdf"
        onChange={handlePdfUpload}
        style={{ display: 'none' }}
      />

      {/* ChatGPT-style Floating Bottom Pill Input Container */}
      <div style={{
        padding: '0 16% 24px 16%',
        backgroundColor: '#0d0d0d'
      }}>
        {/* Quick Shortcut Buttons Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '8px',
          marginBottom: '12px'
        }}>
          <button
            onClick={() => handleSend('/specialty knee pain')}
            style={{
              backgroundColor: '#171717',
              color: '#d4d4d4',
              border: '1px solid #262626',
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
          >
            <strong style={{ color: '#60a5fa' }}>/specialty</strong> – Organ hospital discovery
          </button>
          <button
            onClick={() => handleSend('/comfort gastritis diet')}
            style={{
              backgroundColor: '#171717',
              color: '#d4d4d4',
              border: '1px solid #262626',
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
          >
            <strong style={{ color: '#34d399' }}>/comfort</strong> – Disease diet & comfort guide
          </button>
          <button
            onClick={() => handleSend('/triage heartburn and nausea')}
            style={{
              backgroundColor: '#171717',
              color: '#d4d4d4',
              border: '1px solid #262626',
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
          >
            <strong style={{ color: '#fbbf24' }}>/triage</strong> – Symptom likelihood ranking
          </button>
          <button
            onClick={() => handleSend('/report_reader HbA1c 7.2%')}
            style={{
              backgroundColor: '#171717',
              color: '#d4d4d4',
              border: '1px solid #262626',
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
          >
            <strong style={{ color: '#c084fc' }}>/report_reader</strong> – Lab value explainer
          </button>
          <button
            onClick={() => handleSend('/emergency severe chest pain')}
            style={{
              backgroundColor: '#171717',
              color: '#d4d4d4',
              border: '1px solid #262626',
              borderRadius: '10px',
              padding: '8px 12px',
              fontSize: '0.78rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
          >
            <strong style={{ color: '#f87171' }}>/emergency</strong> – 24/7 ER assistance
          </button>
        </div>

        {/* Floating Input Pill */}
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          accept=".pdf,.txt,.csv,.json,.png,.jpg,.jpeg,.webp"
          onChange={handlePdfUpload}
        />
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: '#212121',
          borderRadius: '24px',
          border: '1px solid #2f2f2f',
          padding: '8px 16px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
        }}>
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Attach Medical Document or Prescription Photo"
            style={{
              background: 'none',
              border: 'none',
              color: pdfFileName ? '#3b82f6' : '#a3a3a3',
              fontSize: '1.3rem',
              cursor: 'pointer',
              marginRight: '12px',
              lineHeight: 1
            }}
          >
            +
          </button>
          <input
            type="text"
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#ffffff',
              fontSize: '0.95rem'
            }}
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: input.trim() ? '#ffffff' : '#404040',
              color: input.trim() ? '#000000' : '#a3a3a3',
              border: 'none',
              cursor: input.trim() ? 'pointer' : 'default',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '1.1rem',
              marginLeft: '8px',
              transition: 'all 0.2s ease'
            }}
          >
            ↑
          </button>
        </div>
        <div style={{ textAlign: 'center', fontSize: '0.72rem', color: '#737373', marginTop: '8px' }}>
          Health Assistant AI can make mistakes. Verify important medical decisions with your physician.
        </div>
      </div>
    </div>
  );
}
