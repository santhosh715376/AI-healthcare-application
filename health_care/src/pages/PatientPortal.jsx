import React, { useState } from 'react';
import PrescriptionCard from '../components/PrescriptionCard.jsx';
import ChatPage from './ChatPage.jsx';
import TimelinePage from './TimelinePage.jsx';

export default function PatientPortal() {
  const [patientMobile] = useState('+91 9876543210');
  const [patientId] = useState('pat-1001');
  const [activeSubTab, setActiveSubTab] = useState('ocr'); // 'ocr' | 'chat' | 'timeline'

  // OCR Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [ocrParsedData, setOcrParsedData] = useState(null);
  const [loadingOcr, setLoadingOcr] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setOcrParsedData(null);
    }
  };

  const handleParseOcrClick = async () => {
    if (!selectedFile) {
      alert('Please select a prescription image file first.');
      return;
    }
    setLoadingOcr(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await fetch('http://localhost:8000/api/prescriptions/parse-image', {
        method: 'POST',
        body: formData,
      });
      const json = await res.json();
      setOcrParsedData(json);
    } catch (err) {
      console.error('Gemini OCR Error:', err);
      alert('Error parsing paper slip with Gemini OCR.');
    } finally {
      setLoadingOcr(false);
    }
  };

  const handleSaveOcrToTimeline = async () => {
    if (!ocrParsedData) return;
    try {
      await fetch('http://localhost:8000/api/timeline/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ocrParsedData),
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      console.error('Error saving OCR data:', err);
      alert('Error saving OCR record to timeline.');
    }
  };

  return (
    <div className="patient-portal-container">
      {/* Top Patient Header Bar */}
      <div style={{
        backgroundColor: '#1f2937',
        padding: '12px 20px',
        borderBottom: '1px solid #374151',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#10b981' }}>👤 Patient Health Portal</span>
          <span style={{
            backgroundColor: '#064e3b',
            color: '#a7f3d0',
            fontSize: '0.78rem',
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 600
          }}>
            Phone: {patientMobile} (ID: {patientId})
          </span>
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
          className={`tab-btn ${activeSubTab === 'ocr' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('ocr')}
        >
          📷 Scan Paper Prescription (Gemini OCR)
        </button>
        <button
          className={`tab-btn ${activeSubTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('chat')}
        >
          💬 Personal Health AI Assistant
        </button>
        <button
          className={`tab-btn ${activeSubTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('timeline')}
        >
          📋 My Medical Records Timeline
        </button>
      </div>

      {/* SUB-TAB 1: OCR Ingestion */}
      {activeSubTab === 'ocr' && (
        <div className="workspace-split">
          <div className="pane">
            <div className="pane-header">
              <span className="pane-title">📷 Upload Handwritten Paper Prescription</span>
            </div>
            <label className="dropzone-full">
              <input type="file" accept="image/*" onChange={handleFileChange} style={{ display: 'none' }} />
              {previewUrl ? (
                <img src={previewUrl} alt="Paper Slip Preview" className="img-preview-full" />
              ) : (
                <div style={{ textAlign: 'center', color: '#9ca3af' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '12px' }}>📤</div>
                  <div style={{ fontWeight: 600, color: '#e5e7eb', fontSize: '1.1rem' }}>
                    Click or Drag & Drop Prescription Image Here
                  </div>
                  <div style={{ fontSize: '0.85rem', marginTop: '6px' }}>
                    Gemini 2.0 Flash Vision will extract medicines & dosages automatically
                  </div>
                </div>
              )}
            </label>
          </div>

          <div className="pane">
            <div className="pane-header">
              <span className="pane-title">✨ Extracted Prescription Record</span>
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
                ✅ OCR Prescription Saved to Your Timeline!
              </div>
            )}

            {ocrParsedData ? (
              <>
                <PrescriptionCard data={ocrParsedData} onUpdate={(updated) => setOcrParsedData(updated)} />
                <div style={{ marginTop: '20px' }}>
                  <button
                    className="action-btn"
                    onClick={handleSaveOcrToTimeline}
                    style={{
                      width: '100%',
                      backgroundColor: '#10b981',
                      padding: '14px',
                      fontSize: '1rem',
                      justifyContent: 'center'
                    }}
                  >
                    🏥 Save to My Timeline
                  </button>
                </div>
              </>
            ) : (
              <div style={{ color: '#9ca3af', fontStyle: 'italic', marginTop: '40px', textAlign: 'center' }}>
                Upload an image in the left pane and click "⚡ Parse Image with Gemini OCR" below.
              </div>
            )}
          </div>

          {/* Floating Gemini OCR Parse Button Bar */}
          <div className="mic-floating-bar">
            <button
              className="action-btn"
              onClick={handleParseOcrClick}
              disabled={loadingOcr || !selectedFile}
              style={{
                backgroundColor: selectedFile ? '#3b82f6' : '#374151',
                padding: '12px 28px',
                borderRadius: '25px',
                fontSize: '0.95rem',
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)'
              }}
            >
              {loadingOcr ? '⚡ Extracting with Gemini 2.0...' : '⚡ Parse Image with Gemini OCR'}
            </button>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: Consumer Health Chatbot */}
      {activeSubTab === 'chat' && <ChatPage />}

      {/* SUB-TAB 3: Patient Medical History Timeline */}
      {activeSubTab === 'timeline' && <TimelinePage />}
    </div>
  );
}
