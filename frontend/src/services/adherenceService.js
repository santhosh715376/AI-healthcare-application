import { apiRequest } from './api';

export async function getPatientAdherence(patientIdOrPhone) {
  const cleanId = String(patientIdOrPhone).replace(/\D/g, '') || '100001';
  return apiRequest(`/api/adherence/patient/${encodeURIComponent(cleanId)}`);
}

export async function checkinDose({ scheduleId, patientId, routineSlot, scheduledDate }) {
  return apiRequest('/api/adherence/checkin', {
    method: 'POST',
    body: JSON.stringify({
      schedule_id: scheduleId,
      patient_id: patientId,
      routine_slot: routineSlot,
      scheduled_date: scheduledDate,
    }),
  });
}

export async function createAdherenceSchedule(schedulePayload) {
  return apiRequest('/api/adherence/schedule', {
    method: 'POST',
    body: JSON.stringify(schedulePayload),
  });
}

export async function getPatientProfile(phone) {
  return apiRequest(`/api/patient/profile?phone=${encodeURIComponent(phone)}`);
}
