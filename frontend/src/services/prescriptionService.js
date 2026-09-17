import { apiRequest } from './api';

export async function parsePrescriptionImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  return apiRequest('/api/prescriptions/parse-image', {
    method: 'POST',
    body: formData,
  });
}

export async function parsePrescriptionVoice(rawText, patientId, source = 'doctor_voice') {
  return apiRequest('/api/prescriptions/parse', {
    method: 'POST',
    body: JSON.stringify({ rawText, patientId, source }),
  });
}

export async function savePrescriptionToTimeline(prescriptionPayload) {
  return apiRequest('/api/timeline/save', {
    method: 'POST',
    body: JSON.stringify(prescriptionPayload),
  });
}

export async function getPatientTimeline(patientId, doctorId = null) {
  const query = doctorId ? `?doctor_id=${encodeURIComponent(doctorId)}` : '';
  return apiRequest(`/api/timeline/${encodeURIComponent(patientId)}${query}`);
}
