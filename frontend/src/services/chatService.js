import { apiRequest, DEFAULT_LAT, DEFAULT_LNG } from './api';

export async function sendPatientAdvisorMessage({ message, patientName, patientPhone, pdfContext, lat, lng }) {
  return apiRequest('/api/chat/patient-advisor', {
    method: 'POST',
    body: JSON.stringify({
      message,
      patientName: patientName || 'Patient',
      patientPhone: patientPhone || '9876543210',
      pdfContext: pdfContext || null,
      lat: lat || DEFAULT_LAT,
      lng: lng || DEFAULT_LNG,
    }),
  });
}

export async function sendChatMessage({ message, sessionId = 'default', patientId, role = 'patient' }) {
  return apiRequest('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({
      message,
      sessionId,
      patientId,
      role,
    }),
  });
}
