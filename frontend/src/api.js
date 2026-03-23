const BASE_URL = 'http://127.0.0.1:8080';

export function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return fetch(`${BASE_URL}/upload/`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json());
}

export function getUploadedLogs() {
  return fetch(`${BASE_URL}/upload/logs`).then(r => r.json());
}

export function analyzeAllMachines() {
  return fetch(`${BASE_URL}/analyze`, { method:'POST' }).then(r => r.json());
}

export function getAllMachines() {
  return fetch(`${BASE_URL}/machines`).then(r => r.json());
}

export function getSchedule() {
  return fetch(`${BASE_URL}/schedule`).then(r => r.json());
}

export function getSummary() {
  return fetch(`${BASE_URL}/summary`).then(r => r.json());
}

export function queryAI(question) {
  return fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  }).then(r => r.json());
}