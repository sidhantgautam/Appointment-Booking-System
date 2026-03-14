import axios from 'axios';

// API Base Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});


apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);


apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface TextAgentRequest {
  text: string;
  session_id?: string;
  return_in_original_language?: boolean;
}

export interface TextAgentResponse {
  request_id: string;
  session_id: string;
  original_text: string;
  detected_language: string;
  language_name: string;
  translated_text: string;
  agent_result: {
    message?: string;
    error?: string;
    action?: string;
    result?: any;
  };
  response_translated?: string;
  performance: {
    total_duration_ms: number;
    component_timings: {
      language_detection_ms: number;
      translation_ms: number;
      llm_reasoning_ms: number;
    };
  };
}

export interface VoiceAgentResponse {
  request_id: string;
  session_id: string;
  transcription: string;
  detected_language: string;
  language_name: string;
  translated_text: string;
  agent_result: {
    message?: string;
    error?: string;
    action?: string;
    result?: any;
  };
  response_translated?: string;
  performance: {
    total_duration_ms: number;
    component_timings: {
      stt_processing_ms: number;
      language_detection_ms: number;
      translation_ms: number;
      llm_reasoning_ms: number;
    };
    within_target_latency: boolean;
    target_latency_ms: number;
  };
}

export interface Patient {
  id: number;
  name: string;
  language: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialization: string;
}

export interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  time: string;
  patient?: Patient;
  doctor?: Doctor;
}

export interface SessionMemory {
  session_id: string;
  memory: Record<string, any>;
}

export interface ConversationHistory {
  session_id: string;
  conversation_history: Array<{
    timestamp: string;
    sender: string;
    message: string;
  }>;
  message_count: number;
}

// API Functions
export class VoiceAIAPI {
  // Text Agent
  static async sendTextMessage(request: TextAgentRequest): Promise<TextAgentResponse> {
    const response = await apiClient.post('/ai/agent', request);
    return response.data;
  }

  // Voice Agent
  static async sendVoiceMessage(
    audioFile: File, 
    sessionId?: string, 
    returnInOriginalLanguage: boolean = true
  ): Promise<VoiceAgentResponse> {
    const formData = new FormData();
    formData.append('file', audioFile);
    
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    params.append('return_in_original_language', returnInOriginalLanguage.toString());

    const response = await apiClient.post(`/voice/agent?${params.toString()}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Session Management
  static async getSessionMemory(sessionId: string): Promise<SessionMemory> {
    const response = await apiClient.get(`/ai/session/${sessionId}`);
    return response.data;
  }

  static async getConversationHistory(sessionId: string): Promise<ConversationHistory> {
    const response = await apiClient.get(`/ai/session/${sessionId}/history`);
    return response.data;
  }

  static async clearSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/ai/session/${sessionId}`);
  }

  // Patients
  static async getPatients(): Promise<Patient[]> {
    const response = await apiClient.get('/patients/');
    return response.data;
  }

  static async getPatient(id: number): Promise<Patient> {
    const response = await apiClient.get(`/patients/${id}`);
    return response.data;
  }

  static async createPatient(patient: Omit<Patient, 'id'>): Promise<Patient> {
    const response = await apiClient.post('/patients/', patient);
    return response.data;
  }

  // Doctors
  static async getDoctors(): Promise<Doctor[]> {
    const response = await apiClient.get('/appointments/doctors');
    return response.data;
  }

  static async getDoctor(id: number): Promise<Doctor> {
    const response = await apiClient.get(`/appointments/doctors/${id}`);
    return response.data;
  }

  // Appointments
  static async getAppointments(): Promise<Appointment[]> {
    const response = await apiClient.get('/appointments/');
    return response.data;
  }

  static async getPatientAppointments(patientId: number): Promise<Appointment[]> {
    const response = await apiClient.get(`/appointments/patient/${patientId}`);
    return response.data;
  }

  static async createAppointment(appointment: {
    patient_id: number;
    doctor_id: number;
    time: string;
  }): Promise<Appointment> {
    const response = await apiClient.post('/appointments/', appointment);
    return response.data;
  }

  // Health Check
  static async healthCheck(): Promise<{ message: string }> {
    const response = await apiClient.get('/');
    return response.data;
  }
}

export default VoiceAIAPI;