// PupilPrep Frontend API Client
const API_BASE = 'http://localhost:8080/api';

const API = {
  call: async (endpoint, options = {}) => {
    try {
      console.log('API Request:', endpoint, options.body ? JSON.parse(options.body) : 'no body');
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('API Error Response:', errorData);
        throw new Error(`HTTP ${response.status}${errorData?.detail ? ': ' + JSON.stringify(errorData.detail) : ''}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      showToast(error.message, 'error');
      throw error;
    }
  },
  
  // Content Generation
  generateAHS: (data) => API.call('/v1/contentGenerationForAHS', { method: 'POST', body: JSON.stringify(data) }),
  generateRemedy: (data) => API.call('/v1/contentGenerationForRemedies', { method: 'POST', body: JSON.stringify(data) }),
  getJobStatus: (jobId) => API.call(`/v1/jobs/${jobId}`),
  getJobContent: (jobId) => API.call(`/v1/jobs/${jobId}/content`),
  
  // Assessment
  generateAssessment: (data) => API.call('/assessments/generate', { method: 'POST', body: JSON.stringify(data) }),
  getAssessmentStatus: (jobId) => API.call(`/assessments/status/${jobId}`),
  getAssessment: (id) => API.call(`/assessments/${id}`),
  
  // Timetable
  getDailySchedule: (params) => API.call(`/timetable/daily-schedule?${new URLSearchParams(params)}`),
  
  // Reports
  getStudentReport: (classId, studentId) => API.call(`/student_report/${classId}/${studentId}`),
  getClassReport: (board, grade, section) => API.call(`/class_report/board/${board}/grade/${grade}/section/${section}`)
};

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<div style="display:flex;gap:1rem;align-items:center;"><span>${type === 'error' ? '❌' : '✅'}</span><span>${message}</span></div>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

async function pollJobStatus(jobId, callback) {
  let attempts = 0;
  const poll = async () => {
    if (attempts++ > 60) return;
    try {
      const status = await API.getJobStatus(jobId);
      callback(status);
      if (status.status !== 'completed' && status.status !== 'failed') {
        setTimeout(poll, 2000);
      }
    } catch (e) {}
  };
  poll();
}
