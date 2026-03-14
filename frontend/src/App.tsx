import React, { useState, useEffect } from 'react';
import { 
  Stethoscope, 
  Users, 
  Calendar, 
  Activity,
  RefreshCw,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { VoiceConversation } from './components/VoiceConversation';
import { VoiceAIAPI, Patient, Doctor, Appointment } from './services/api';

interface AppState {
  currentSessionId: string;
  patients: Patient[];
  doctors: Doctor[];
  appointments: Appointment[];
  isConnected: boolean;
  loading: boolean;
  error: string | null;
}

function App() {
  const [state, setState] = useState<AppState>({
    currentSessionId: `session_${Date.now()}`,
    patients: [],
    doctors: [],
    appointments: [],
    isConnected: false,
    loading: true,
    error: null,
  });

  const [activeTab, setActiveTab] = useState<'conversation' | 'patients' | 'appointments' | 'performance'>('conversation');

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Test backend connection
      await VoiceAIAPI.healthCheck();
      
      // Load initial data
      const [patients, doctors, appointments] = await Promise.all([
        VoiceAIAPI.getPatients().catch(() => []),
        VoiceAIAPI.getDoctors().catch(() => []),
        VoiceAIAPI.getAppointments().catch(() => []),
      ]);

      setState(prev => ({
        ...prev,
        patients,
        doctors,
        appointments,
        isConnected: true,
        loading: false,
      }));

    } catch (error) {
      console.error('Failed to initialize app:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to connect to backend. Please ensure the API server is running.',
        isConnected: false,
        loading: false,
      }));
    }
  };

  const refreshData = async () => {
    try {
      const [patients, doctors, appointments] = await Promise.all([
        VoiceAIAPI.getPatients(),
        VoiceAIAPI.getDoctors(),
        VoiceAIAPI.getAppointments(),
      ]);

      setState(prev => ({
        ...prev,
        patients,
        doctors,
        appointments,
      }));
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
  };

  const newSession = () => {
    setState(prev => ({
      ...prev,
      currentSessionId: `session_${Date.now()}`,
    }));
  };

  if (state.loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to Voice AI Clinic...</p>
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h1>
          <p className="text-gray-600 mb-4">{state.error}</p>
          <button
            onClick={initializeApp}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Stethoscope className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Voice AI Clinic</h1>
                <p className="text-sm text-gray-500">Intelligent Appointment Assistant</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${state.isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {state.isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              <button
                onClick={refreshData}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                title="Refresh data"
              >
                <RefreshCw className="w-5 h-5" />
              </button>

              <button
                onClick={newSession}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
              >
                New Session
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-4">
              <nav className="space-y-2">
                <button
                  onClick={() => setActiveTab('conversation')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === 'conversation'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Stethoscope className="w-5 h-5" />
                  <span>Conversation</span>
                </button>

                <button
                  onClick={() => setActiveTab('patients')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === 'patients'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Users className="w-5 h-5" />
                  <span>Patients ({state.patients.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab('appointments')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === 'appointments'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Calendar className="w-5 h-5" />
                  <span>Appointments ({state.appointments.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab('performance')}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === 'performance'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Activity className="w-5 h-5" />
                  <span>Performance</span>
                </button>
              </nav>

              {}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Doctors:</span>
                    <span className="font-medium">{state.doctors.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Patients:</span>
                    <span className="font-medium">{state.patients.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Appointments:</span>
                    <span className="font-medium">{state.appointments.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {}
          <div className="lg:col-span-3">
            {activeTab === 'conversation' && (
              <div className="h-[600px]">
                <VoiceConversation
                  sessionId={state.currentSessionId}
                  onSessionChange={(sessionId) => 
                    setState(prev => ({ ...prev, currentSessionId: sessionId }))
                  }
                />
              </div>
            )}

            {activeTab === 'patients' && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Patients</h2>
                <div className="space-y-3">
                  {state.patients.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No patients found</p>
                  ) : (
                    state.patients.map((patient) => (
                      <div key={patient.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                        <div>
                          <h3 className="font-medium text-gray-900">{patient.name}</h3>
                          <p className="text-sm text-gray-500">ID: {patient.id} • Language: {patient.language}</p>
                        </div>
                        <button
                          onClick={() => {
                            setState(prev => ({ 
                              ...prev, 
                              currentSessionId: `patient_${patient.id}_${Date.now()}` 
                            }));
                            setActiveTab('conversation');
                          }}
                          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                        >
                          Chat
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'appointments' && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Appointments</h2>
                  <button
                    onClick={refreshData}
                    className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                    title="Refresh appointments"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh</span>
                  </button>
                </div>
                <div className="space-y-3">
                  {state.appointments.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No appointments found</p>
                  ) : (
                    state.appointments.map((appointment) => (
                      <div key={appointment.id} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">
                              Appointment #{appointment.id}
                            </h3>
                            <p className="text-sm text-gray-500">
                              Patient ID: {appointment.patient_id} • Doctor ID: {appointment.doctor_id}
                            </p>
                            <p className="text-sm text-gray-600 mt-1">
                              {new Date(appointment.time).toLocaleString()}
                            </p>
                          </div>
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === 'performance' && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Monitoring</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-primary-50 rounded-lg">
                    <h3 className="font-medium text-primary-900">Target Latency</h3>
                    <p className="text-2xl font-bold text-primary-600">450ms</p>
                    <p className="text-sm text-primary-700">Voice pipeline target</p>
                  </div>
                  
                  <div className="p-4 bg-success-50 rounded-lg">
                    <h3 className="font-medium text-success-900">System Status</h3>
                    <p className="text-2xl font-bold text-success-600">Online</p>
                    <p className="text-sm text-success-700">All services operational</p>
                  </div>
                  
                  <div className="p-4 bg-warning-50 rounded-lg">
                    <h3 className="font-medium text-warning-900">Languages</h3>
                    <p className="text-2xl font-bold text-warning-600">3</p>
                    <p className="text-sm text-warning-700">English, Hindi, Tamil</p>
                  </div>
                  
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-medium text-gray-900">Session</h3>
                    <p className="text-lg font-mono text-gray-600 truncate">{state.currentSessionId}</p>
                    <p className="text-sm text-gray-700">Current session ID</p>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="font-medium text-gray-900 mb-3">Features</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Voice Recognition</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Multi-language Support</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Performance Monitoring</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Conversation Memory</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Appointment Booking</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-success-500" />
                      <span className="text-sm">Outbound Reminders</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;