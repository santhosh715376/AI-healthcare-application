import React, { useState, useEffect, useRef } from 'react';
import PrescriptionCard from '../components/PrescriptionCard.jsx';
import ChatPage from './ChatPage.jsx';
import TimelinePage from './TimelinePage.jsx';
import HospitalMap from '../components/HospitalMap.jsx';
import EmergencyFilterPane from '../components/EmergencyFilterPane.jsx';

export default function PatientPortal({ currentUser }) {
  const patientMobile = currentUser?.phone || '9876543210';
  const patientId = currentUser?.id || '100001';
  const [activeSubTab, setActiveSubTab] = useState('ocr'); // 'ocr' | 'chat' | 'timeline' | 'mapping'

  // OCR Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [ocrParsedData, setOcrParsedData] = useState(null);
  const [loadingOcr, setLoadingOcr] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Emergency Spatial Mapping State
  const [searchQuery, setSearchQuery] = useState('');
  const [radiusKm, setRadiusKm] = useState(15);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [locationEnabled, setLocationEnabled] = useState(false);

  const cardRefs = useRef({});

  // Request Browser Geolocation
  const requestLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          setLocationEnabled(true);
        },
        (err) => {
          console.warn('Geolocation access denied or unavailable:', err);
          setLocationEnabled(false);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  };

  useEffect(() => {
    requestLocation();
  }, []);

  // Fetch Hospitals from FastAPI SQLite Endpoint
  const fetchHospitals = async () => {
    try {
      const lat = userLocation ? userLocation.lat : 11.0168;
      const lng = userLocation ? userLocation.lng : 76.9558;
      let url = `http://localhost:8000/api/hospitals?lat=${lat}&lng=${lng}&radiusKm=${radiusKm}`;

      if (searchQuery.trim()) {
        url += `&query=${encodeURIComponent(searchQuery.trim())}`;
      }
      if (selectedCategory && selectedCategory !== 'All') {
        url += `&specialty=${encodeURIComponent(selectedCategory)}`;
      }

      const res = await fetch(url);
      const data = await res.json();
      setHospitals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching spatial hospital records:', err);
    }
  };

  useEffect(() => {
    if (activeSubTab === 'mapping') {
      fetchHospitals();
    }
  }, [activeSubTab, radiusKm, searchQuery, selectedCategory, userLocation]);

  const handleSelectHospital = (id) => {
    setSelectedHospitalId(id);
    if (cardRefs.current[id]) {
      cardRefs.current[id].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

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
      console.error('Error parsing prescription OCR:', err);
      alert('Failed to parse paper prescription image.');
    } finally {
      setLoadingOcr(false);
    }
  };

  const handleSaveOcrToTimeline = async () => {
    if (!ocrParsedData) return;
    try {
      const payloadToSave = {
        ...ocrParsedData,
        patientId: currentUser?.id ? String(currentUser.id) : '100001',
        patientPhone: currentUser?.phone || '9876543210',
      };

      await fetch('http://localhost:8000/api/timeline/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadToSave),
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      console.error('Error saving OCR data:', err);
      alert('Error saving OCR record to timeline.');
    }
  };

  return (
    <div className="patient-portal-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
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
        <button
          className={`tab-btn ${activeSubTab === 'mapping' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('mapping')}
        >
          🗺️ Mapping
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
                    🏥 Confirm & Save to Patient Timeline Record
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
      {activeSubTab === 'timeline' && <TimelinePage patientId={patientMobile} />}

      {/* SUB-TAB 4: Emergency Geospatial Hospital Discovery Mapping */}
      {activeSubTab === 'mapping' && (
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden', height: 'calc(100vh - 120px)' }}>
          <EmergencyFilterPane
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            radiusKm={radiusKm}
            onRadiusChange={setRadiusKm}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            hospitals={hospitals}
            selectedHospitalId={selectedHospitalId}
            onSelectHospital={handleSelectHospital}
            locationEnabled={locationEnabled}
            onRequestLocation={requestLocation}
            cardRefs={cardRefs}
          />
          <div style={{ flex: 1, height: '100%', position: 'relative' }}>
            <HospitalMap
              hospitals={hospitals}
              center={userLocation || { lat: 11.0168, lng: 76.9558 }}
              radiusKm={radiusKm}
              userLocation={userLocation}
              selectedHospitalId={selectedHospitalId}
              onSelectHospital={handleSelectHospital}
            />
          </div>
        </div>
      )}
    </div>
  );
}
