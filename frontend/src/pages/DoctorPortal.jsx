import React, { useState, useEffect, useRef } from 'react';
import PrescriptionCard from '../components/PrescriptionCard.jsx';
import ChatBubble from '../components/ChatBubble.jsx';
import TimelinePage from './TimelinePage.jsx';

export default function DoctorPortal({ currentUser }) {
  const docLicense = currentUser?.doc_license || 'NMC-TN-88492';

  // Active Patient Lookup State (Pure 10-digit mobile number)
  const [searchQuery, setSearchQuery] = useState('9876543210');
  const [activePatientId, setActivePatientId] = useState('9876543210');

  // Sub-navigation inside Doctor Portal
  const [activeSubTab, setActiveSubTab] = useState('prescribe'); // 'prescribe' | 'clinical_chat' | 'history'

  // Voice STT Prescribing State
  const [transcript, setTranscript] = useState(
    'Doctor prescribed Syp Calpol 250/5 5ml three times a day after food for 5 days. Also Syp Meftal P 3ml twice a day for fever.'
  );
  const [isRecording, setIsRecording] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [isAutoParsing, setIsAutoParsing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Doctor Clinical Chatbot State
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [sessionId] = useState(() => `doc-session-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`);

  const recognitionRef = useRef(null);
  const debounceTimerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto-parse voice transcript with Groq Llama 3.3 70B
  const parseWithGroq = async (textToParse) => {
    if (!textToParse || !textToParse.trim()) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsAutoParsing(true);
    try {
      const res = await fetch('http://localhost:8000/api/prescriptions/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({ rawText: textToParse, patientId: activePatientId, source: 'doctor_voice' }),
      });
      const json = await res.json();
      setParsedData(json);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Groq Auto-Parse Error:', err);
      }
    } finally {
      setIsAutoParsing(false);
    }
  };

  useEffect(() => {
    if (activeSubTab !== 'prescribe') return;
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(() => {
      if (transcript.trim()) parseWithGroq(transcript);
    }, 700);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [transcript, activeSubTab]);

  useEffect(() => {
    parseWithGroq(transcript);
  }, []);

  // Web Speech API Setup for Doctor Mic
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTranscript((prev) => (prev ? prev + ' ' + finalTranscript : finalTranscript));
        }
      };

      recognitionRef.current.onerror = () => setIsRecording(false);
      recognitionRef.current.onend = () => setIsRecording(false);
    }
  }, []);

  const toggleRecording = async () => {
    if (!recognitionRef.current) {
      alert('Web Speech API is not supported in this browser. Type in the text area directly.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          await navigator.mediaDevices.getUserMedia({
            audio: { autoGainControl: true, noiseSuppression: true, echoCancellation: true },
          });
        }
      } catch (e) {
        console.warn('Audio constraint warning:', e);
      }
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  // Doctor Save Prescription to Timeline Record
  const handleSaveToRecord = async (dataToSave) => {
    const payload = dataToSave || parsedData;
    if (!payload) return;

    try {
      await fetch('http://localhost:8000/api/timeline/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      console.error('Error saving timeline record:', err);
      alert('Failed to save prescription to patient timeline.');
    }
  };

  // Doctor Clinical Chatbot Message Handler (role: "doctor")
  const handleDoctorChatSend = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userText = chatInput.trim();
    setChatInput('');

    setChatMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setChatLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: userText, role: 'doctor' }),
      });
      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      console.error('Clinical Chat Error:', err);
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Connection error. Ensure backend server is running.' },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handlePatientSearch = () => {
    if (!searchQuery.trim()) return;
    const clean = searchQuery.replace(/\D/g, '') || searchQuery.trim();
    setActivePatientId(clean);
  };

  return (
    <div className="doctor-portal-container">
      {/* Top Doctor Header Bar */}
      <div style={{
        backgroundColor: '#1f2937',
        padding: '12px 20px',
        borderBottom: '1px solid #374151',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#60a5fa' }}>👨‍⚕️ Doctor OPD Workspace</span>
          <span style={{
            backgroundColor: '#1e3a8a',
            color: '#93c5fd',
            fontSize: '0.78rem',
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 600
          }}>
            License: {docLicense} (NMC Verified)
          </span>
        </div>

        {/* Patient Mobile Search Bar (Pure 10-digit) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>Patient OPD Search:</span>
          <input
            type="text"
            className="transcript-area"
            style={{ width: '190px', height: '32px', fontSize: '0.85rem' }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="10-digit Phone or Name"
          />
          <button
            onClick={handlePatientSearch}
            style={{
              backgroundColor: '#2563eb',
              color: '#fff',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            🔍 Search OPD
          </button>
        </div>
      </div>

      {/* Sub-tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '10px',
        padding: '10px 20px',
        backgroundColor: '#111827',
        borderBottom: '1px solid #1f2937'
      }}>
        <button
          className={`tab-btn ${activeSubTab === 'prescribe' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('prescribe')}
        >
          🎙️ Voice Prescription Capture
        </button>
        <button
          className={`tab-btn ${activeSubTab === 'clinical_chat' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('clinical_chat')}
        >
          🧬 Doctor Clinical Assistant (RAG Chatbot)
        </button>
        <button
          className={`tab-btn ${activeSubTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('history')}
        >
          📋 Patient Records Timeline ({activePatientId})
        </button>
      </div>

      {/* SUB-TAB 1: Voice STT Capture */}
      {activeSubTab === 'prescribe' && (
        <div className="workspace-split">
          <div className="pane">
            <div className="pane-header">
              <span className="pane-title">📝 Doctor Spoken Transcript Editor</span>
              {isAutoParsing && (
                <span style={{ fontSize: '0.82rem', color: '#10b981', fontWeight: 600 }}>
                  ⚡ Auto-structuring with Groq Llama 3.3...
                </span>
              )}
            </div>
            <textarea
              className="transcript-area"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Speak prescription into mic or type here..."
            />
          </div>

          <div className="pane">
            <div className="pane-header">
              <span className="pane-title">✨ Auto-Formatted Header-Body-Tail Card</span>
            </div>

            {saveSuccess && (
              <div style={{
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                color: '#10b981',
                padding: '10px 14px',
                borderRadius: '8px',
                marginBottom: '16px',
                fontWeight: 600,
                fontSize: '0.9rem'
              }}>
                ✅ Prescription Verified & Saved to Patient Timeline!
              </div>
            )}

            {parsedData ? (
              <>
                <PrescriptionCard data={parsedData} onUpdate={(updated) => setParsedData(updated)} />
                <div style={{ marginTop: '20px' }}>
                  <button
                    className="action-btn"
                    onClick={() => handleSaveToRecord(parsedData)}
                    style={{
                      width: '100%',
                      backgroundColor: '#10b981',
                      padding: '14px',
                      fontSize: '1rem',
                      justifyContent: 'center'
                    }}
                  >
                    🏥 Confirm & Save to Patient Timeline Record
                  </button>
                </div>
              </>
            ) : (
              <div style={{ color: '#9ca3af', fontStyle: 'italic', marginTop: '40px', textAlign: 'center' }}>
                Speak into microphone to generate live structured prescription card.
              </div>
            )}
          </div>

          {/* Floating Push to Speak Button */}
          <div className="mic-floating-bar">
            <button
              className={`mic-button ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
              title="Click Push to Speak"
            >
              {isRecording ? '⏹️' : '🎙️'}
            </button>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e5e7eb' }}>
              {isRecording ? 'Doctor Mic Active... (Speaking)' : 'Doctor Push to Speak'}
            </span>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: Doctor Clinical Research Chatbot */}
      {activeSubTab === 'clinical_chat' && (
        <div className="chat-thread-container" style={{ height: 'calc(100vh - 150px)' }}>
          <div className="chat-thread-header">
            <span>🧬 Clinical Research AI Assistant (Patient Context: {activePatientId})</span>
            <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
              Guardrails Lifted for Physician Disease Research & Interaction Analysis
            </span>
          </div>

          <div className="chat-messages-area">
            {chatMessages.length === 0 ? (
              <div style={{ textAlign: 'center', marginTop: '40px', color: '#9ca3af' }}>
                <h3>Ask clinical research, dosage, or drug interaction queries for this patient case</h3>
                <p style={{ fontSize: '0.85rem', marginTop: '8px' }}>
                  Example: <em>"What second-line antibiotics can replace Penicillin for this patient?"</em>
                </p>
              </div>
            ) : (
              chatMessages.map((msg, index) => (
                <ChatBubble key={index} role={msg.role} content={msg.content} />
              ))
            )}
            {chatLoading && <div style={{ color: '#9ca3af', fontStyle: 'italic', padding: '12px' }}>Analyzing clinical context...</div>}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-bottom-bar-wrapper">
            <div className="chat-input-pill-bottom">
              <input
                type="text"
                className="chat-input-field-bottom"
                placeholder="Ask clinical research query..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleDoctorChatSend()}
              />
              <button className="chat-send-btn-circle" onClick={handleDoctorChatSend} disabled={!chatInput.trim() || chatLoading}>
                ↑
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: Patient Records Timeline */}
      {activeSubTab === 'history' && <TimelinePage patientId={activePatientId} doctorId={currentUser?.id} />}
    </div>
  );
}
