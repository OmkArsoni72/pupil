import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }

  // Authentication
  async login(email: string, password: string) {
    const response = await this.client.post('/v1/users/login', { email, password });
    return response.data;
  }

  async register(data: any) {
    const response = await this.client.post('/v1/users/register', data);
    return response.data;
  }

  async verifyOTP(email: string, otp: string) {
    const response = await this.client.post('/v1/users/verify-otp', { email, otp });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/v1/users/me');
    return response.data;
  }

  // Content Generation
  async generateAfterHourContent(data: any) {
    const response = await this.client.post('/v1/contentGenerationForAHS', data);
    return response.data;
  }

  async generateRemediationContent(data: any) {
    const response = await this.client.post('/v1/contentGenerationForRemedies', data);
    return response.data;
  }

  // Job Management
  async getJobStatus(jobId: string) {
    const response = await this.client.get(`/v1/jobs/${jobId}`);
    return response.data;
  }

  async pollJobStatus(jobId: string, onProgress?: (progress: number) => void): Promise<any> {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const status = await this.getJobStatus(jobId);
          
          if (onProgress) {
            onProgress(status.progress);
          }

          if (status.status === 'completed') {
            clearInterval(interval);
            resolve(status);
          } else if (status.status === 'failed') {
            clearInterval(interval);
            reject(new Error(status.error || 'Job failed'));
          }
        } catch (error) {
          clearInterval(interval);
          reject(error);
        }
      }, 2000); // Poll every 2 seconds
    });
  }

  // Assessment Management
  async generateAssessment(data: any) {
    const response = await this.client.post('/v1/assessments/generate', data);
    return response.data;
  }

  async getAssessment(assessmentId: string) {
    const response = await this.client.get(`/v1/assessments/${assessmentId}`);
    return response.data;
  }

  async listAssessments(params?: any) {
    const response = await this.client.get('/v1/assessments', { params });
    return response.data;
  }

  // Teacher Classes
  async getTeacherClasses() {
    const response = await this.client.get('/v1/teacher/classes');
    return response.data;
  }

  async getClassDetails(classId: string) {
    const response = await this.client.get(`/v1/teacher/classes/${classId}`);
    return response.data;
  }

  // Sessions
  async getSessions(params?: any) {
    const response = await this.client.get('/v1/sessions', { params });
    return response.data;
  }

  async getSession(sessionId: string) {
    const response = await this.client.get(`/v1/sessions/${sessionId}`);
    return response.data;
  }

  async createSession(data: any) {
    const response = await this.client.post('/v1/sessions', data);
    return response.data;
  }

  async updateSession(sessionId: string, data: any) {
    const response = await this.client.put(`/v1/sessions/${sessionId}`, data);
    return response.data;
  }

  // Student Reports
  async getStudentReport(studentId: string, params?: any) {
    const response = await this.client.get(`/v1/reports/student/${studentId}`, { params });
    return response.data;
  }

  async getClassReport(classId: string, params?: any) {
    const response = await this.client.get(`/v1/reports/class/${classId}`, { params });
    return response.data;
  }

  // Timetable
  async getTimetable(params?: any) {
    const response = await this.client.get('/v1/timetable', { params });
    return response.data;
  }

  async createTimetableEvent(data: any) {
    const response = await this.client.post('/v1/timetable', data);
    return response.data;
  }

  // Question Bank
  async searchQuestions(params: any) {
    const response = await this.client.get('/v1/questions/search', { params });
    return response.data;
  }

  async getQuestion(questionId: string) {
    const response = await this.client.get(`/v1/questions/${questionId}`);
    return response.data;
  }

  // Curriculum
  async getCurriculum(params?: any) {
    const response = await this.client.get('/v1/curriculum', { params });
    return response.data;
  }

  // Generic method for custom requests
  async get(url: string, config?: any) {
    const response = await this.client.get(url, config);
    return response.data;
  }

  async post(url: string, data?: any, config?: any) {
    const response = await this.client.post(url, data, config);
    return response.data;
  }

  async put(url: string, data?: any, config?: any) {
    const response = await this.client.put(url, data, config);
    return response.data;
  }

  async delete(url: string, config?: any) {
    const response = await this.client.delete(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
