import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  MicOff, 
  Send, 
  Loader2, 
  MessageCircle, 
  Volume2,
  Clock,
  User,
  Bot,
  CheckCircle,
  Trash2
} from 'lucide-react';
import { useVoiceRecording, blobToFile } from '../hooks/useVoiceRecording';
import { VoiceAIAPI, TextAgentResponse, VoiceAgentResponse } from '../services/api';
import { LanguageSelectorCompact, LanguageBadge, LanguageOption } from './LanguageSelector';
import { QuickTestButtons } from './QuickTestButtons';
import { AppointmentList, DoctorList, FormattedList } from './AppointmentCard';
import { ErrorDisplay } from './ErrorDisplay';
import { ChatLoadingBubble } from './LoadingIndicator';
import { parseApiError, ParsedError } from '../utils/errorHandler';

interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  language?: string;
  isVoice?: boolean;
  performance?: {
    total_duration_ms: number;
    component_timings: any;
    within_target_latency?: boolean;
  };
  action?: string;
  result?: any;
}

interface VoiceConversationProps {
  sessionId: string;
  onSessionChange?: (sessionId: string) => void;
}

export const VoiceConversation: React.FC<VoiceConversationProps> = ({ 
  sessionId, 
  onSessionChange 
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [textInput, setTextInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [error, setError] = useState<ParsedError | null>(null);
  const [showPerformance, setShowPerformance] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageOption>('auto');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textInputRef = useRef<HTMLInputElement>(null);
  
  const [voiceState, voiceControls] = useVoiceRecording();


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);


  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await VoiceAIAPI.getConversationHistory(sessionId);
        const historyMessages: Message[] = history.conversation_history.map((msg, index) => ({
          id: `history-${index}`,
          type: msg.sender === 'user' ? 'user' : 'agent',
          content: msg.message,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(historyMessages);
      } catch (error) {
        console.error('Failed to load conversation history:', error);
      }
    };
    
    loadHistory();
  }, [sessionId]);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || isLoading) return;

    const userMessage = textInput.trim();
    setTextInput('');
    setError(null);
    setIsLoading(true);

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
      isVoice: false,
    });

    try {
      const response: TextAgentResponse = await VoiceAIAPI.sendTextMessage({
        text: userMessage,
        session_id: sessionId,
        return_in_original_language: true,
      });

      // Add agent response
      let agentMessage = response.agent_result.message || 
                        response.agent_result.result?.message ||
                        response.agent_result.error || 
                        'No response received';

      // Handle successful booking completion
      if (response.agent_result.action === 'book_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        const result = response.agent_result.result;
        if (result.id || result.appointment_id) {
          agentMessage = 'Appointment booked successfully!';
        }
      }

      // Handle booking conflicts
      if (response.agent_result.action === 'booking_conflict' && response.agent_result.message) {
        agentMessage = response.agent_result.message;
      }

      // Handle successful cancellation
      if (response.agent_result.action === 'cancel_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        agentMessage = 'Appointment cancelled successfully!';
      }

      // Handle successful rescheduling
      if (response.agent_result.action === 'reschedule_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        agentMessage = 'Appointment rescheduled successfully!';
      }

      // Handle delete all appointments
      if (response.agent_result.action === 'delete_all_appointments' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'All appointments deleted successfully!';
      }

      // Handle create patient
      if (response.agent_result.action === 'create_patient' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'Patient created successfully!';
      }

      // Handle list patients
      if (response.agent_result.action === 'list_patients' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'Patients listed successfully!';
      }

      addMessage({
        type: 'agent',
        content: agentMessage,
        language: response.detected_language,
        performance: response.performance,
        action: response.agent_result.action,
        result: response.agent_result.result,
      });

    } catch (error) {
      console.error('Text message error:', error);
      const parsedError = parseApiError(error);
      setError(parsedError);
      
      addMessage({
        type: 'agent',
        content: parsedError.message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceSubmit = async () => {
    if (!voiceState.audioBlob || isLoading) return;

    setError(null);
    setIsLoading(true);
    setIsProcessingVoice(true);

    // Add user message placeholder
    const userMessage = addMessage({
      type: 'user',
      content: 'Processing voice message...',
      isVoice: true,
    });

    try {
      const audioFile = blobToFile(voiceState.audioBlob, 'voice-message.webm');
      const response: VoiceAgentResponse = await VoiceAIAPI.sendVoiceMessage(
        audioFile,
        sessionId,
        true
      );


      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, content: response.transcription }
          : msg
      ));

      // Add agent response
      let agentMessage = response.agent_result.message || 
                        response.agent_result.result?.message ||
                        response.agent_result.error || 
                        'No response received';

      // Handle successful booking completion
      if (response.agent_result.action === 'book_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        const result = response.agent_result.result;
        if (result.id || result.appointment_id) {
          agentMessage = 'Appointment booked successfully!';
        }
      }

      // Handle booking conflicts
      if (response.agent_result.action === 'booking_conflict' && response.agent_result.message) {
        agentMessage = response.agent_result.message;
      }

      // Handle successful cancellation
      if (response.agent_result.action === 'cancel_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        agentMessage = 'Appointment cancelled successfully!';
      }

      // Handle successful rescheduling
      if (response.agent_result.action === 'reschedule_appointment' && response.agent_result.result && !response.agent_result.result.message) {
        agentMessage = 'Appointment rescheduled successfully!';
      }

      // Handle delete all appointments
      if (response.agent_result.action === 'delete_all_appointments' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'All appointments deleted successfully!';
      }

      // Handle create patient
      if (response.agent_result.action === 'create_patient' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'Patient created successfully!';
      }

      // Handle list patients
      if (response.agent_result.action === 'list_patients' && response.agent_result.result) {
        agentMessage = response.agent_result.result.message || 'Patients listed successfully!';
      }

      addMessage({
        type: 'agent',
        content: agentMessage,
        language: response.detected_language,
        performance: response.performance,
        action: response.agent_result.action,
        result: response.agent_result.result,
      });

      // Clear recording
      voiceControls.clearRecording();

    } catch (error) {
      console.error('Voice message error:', error);
      const parsedError = parseApiError(error);
      setError(parsedError);
      

      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, content: 'Voice message failed to process' }
          : msg
      ));
      
      addMessage({
        type: 'agent',
        content: parsedError.message,
      });
    } finally {
      setIsLoading(false);
      setIsProcessingVoice(false);
    }
  };

  const clearConversation = async () => {
    try {
      await VoiceAIAPI.clearSession(sessionId);
      setMessages([]);
      setError(null);
      
      // Generate new session ID
      if (onSessionChange) {
        const newSessionId = `session_${Date.now()}`;
        onSessionChange(newSessionId);
      }
    } catch (error) {
      console.error('Failed to clear conversation:', error);
      const parsedError = parseApiError(error);
      setError(parsedError);
    }
  };

  const formatDuration = (ms: number) => {
    return `${ms.toFixed(0)}ms`;
  };

  const getPerformanceColor = (ms: number, target: number = 450) => {
    if (ms <= target) return 'text-green-600';
    if (ms <= target * 1.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderStructuredResult = (message: Message) => {
    if (!message.result) {
      return <p className="text-sm">{message.content}</p>;
    }

    const { action, result } = message;

    // Render appointment list
    if (action === 'list_appointments' && result.appointments) {
      return (
        <div className="space-y-2">
          <AppointmentList 
            appointments={result.appointments}
            message={result.message}
            compact={true}
          />
        </div>
      );
    }

    // Render doctor list
    if (action === 'list_doctors' && result.doctors) {
      return (
        <div className="space-y-2">
          <DoctorList 
            doctors={result.doctors}
            message={result.message}
          />
        </div>
      );
    }


    // Handle booking conflicts with suggested times
    if (action === 'booking_conflict' && result && result.suggested_time) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-orange-700">⚠️ Time slot conflict</p>
          <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs">
            <div className="font-medium text-orange-800 mb-1">Alternative Available</div>
            <div className="text-orange-700">
              {result.message && <div>{result.message}</div>}
              {result.suggested_time && (
                <div className="mt-1 text-xs text-gray-600">
                  Suggested: {new Date(result.suggested_time).toLocaleString()}
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Handle successful booking with detailed confirmation
    if (action === 'book_appointment' && result && (result.id || result.appointment_id)) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-green-700">✅ Appointment booked successfully!</p>
          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
            <div className="font-medium text-green-800 mb-1">Booking Details</div>
            <div className="text-green-700">
              {result.time && (
                <div>Time: {new Date(result.time).toLocaleString()}</div>
              )}
              {result.patient_id && (
                <div>Patient ID: {result.patient_id}</div>
              )}
              {result.doctor_id && (
                <div>Doctor ID: {result.doctor_id}</div>
              )}
              {result.id && (
                <div>Appointment ID: {result.id}</div>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Handle successful cancellation
    if (action === 'cancel_appointment' && result && result.appointment_id) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-red-700">❌ Appointment cancelled successfully!</p>
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
            <div className="font-medium text-red-800 mb-1">Cancellation Details</div>
            <div className="text-red-700">
              <div>Appointment ID: {result.appointment_id}</div>
              {result.message && <div>{result.message}</div>}
            </div>
          </div>
        </div>
      );
    }

    // Handle successful rescheduling
    if (action === 'reschedule_appointment' && result && result.appointment_id) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-blue-700">🔄 Appointment rescheduled successfully!</p>
          <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
            <div className="font-medium text-blue-800 mb-1">Reschedule Details</div>
            <div className="text-blue-700">
              <div>Appointment ID: {result.appointment_id}</div>
              {result.old_time && <div>From: {new Date(result.old_time).toLocaleString()}</div>}
              {result.new_time && <div>To: {new Date(result.new_time).toLocaleString()}</div>}
              {result.message && <div>{result.message}</div>}
            </div>
          </div>
        </div>
      );
    }

    // Handle successful create patient
    if (action === 'create_patient' && result) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-green-700">👤 Patient created successfully!</p>
          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
            <div className="font-medium text-green-800 mb-1">Patient Details</div>
            <div className="text-green-700">
              {result.name && (
                <div>Name: {result.name}</div>
              )}
              {result.id && (
                <div>Patient ID: {result.id}</div>
              )}
              {result.language && (
                <div>Language: {result.language}</div>
              )}
              {result.message && (
                <div className="mt-1">{result.message}</div>
              )}
            </div>
          </div>
        </div>
      );
    }

    // Handle successful delete all appointments
    if (action === 'delete_all_appointments' && result) {
      return (
        <div className="space-y-2">
          <p className="text-sm font-medium text-red-700">🗑️ All appointments deleted!</p>
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
            <div className="font-medium text-red-800 mb-1">Deletion Summary</div>
            <div className="text-red-700">
              {result.deleted_count !== undefined && (
                <div>Deleted: {result.deleted_count} appointment(s)</div>
              )}
              {result.patient_id && (
                <div>Patient ID: {result.patient_id}</div>
              )}
              {result.message && (
                <div className="mt-1">{result.message}</div>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (result.formatted_list && Array.isArray(result.formatted_list)) {
      return (
        <div className="space-y-2">
          <FormattedList 
            items={result.formatted_list}
            message={result.message || message.content}
          />
        </div>
      );
    }


    if (action && result.message) {
      return (
        <div className="space-y-2">
          <p className="text-sm">{result.message}</p>
          {result.appointment && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
              <div className="font-medium text-green-800 mb-1">Appointment Confirmed</div>
              <div className="text-green-700">
                {result.appointment.time && (
                  <div>Time: {result.appointment.time}</div>
                )}
                {result.appointment.doctor_name && (
                  <div>Doctor: Dr {result.appointment.doctor_name}</div>
                )}
                {result.appointment.specialization && (
                  <div>Specialization: {result.appointment.specialization}</div>
                )}
              </div>
            </div>
          )}
        </div>
      );
    }


    return <p className="text-sm">{message.content}</p>;
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <MessageCircle className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Voice AI Assistant</h2>
          <span className="text-sm text-gray-500">Session: {sessionId}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          {}
          <LanguageSelectorCompact
            selectedLanguage={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
          />
          
          <button
            onClick={() => setShowPerformance(!showPerformance)}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            title="Toggle performance metrics"
          >
            <Clock className="w-5 h-5" />
          </button>
          
          <button
            onClick={clearConversation}
            className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-100"
            title="Clear conversation"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-4">
            <div className="text-center text-gray-500 py-8">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Welcome to Voice AI Clinic</p>
              <p className="text-sm">Start a conversation by typing or speaking</p>
            </div>
            
            {}
            <QuickTestButtons
              onTestAction={(message, description) => {
                setTextInput(message);

                setTimeout(() => {
                  const form = document.querySelector('form');
                  if (form) {
                    form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                  }
                }, 100);
              }}
              disabled={isLoading}
            />
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'agent' && (
                  <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                )}
                {message.type === 'user' && (
                  <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                )}
                
                <div className="flex-1">
                  {renderStructuredResult(message)}
                  
                  {}
                  <div className="flex items-center space-x-2 mt-1 text-xs opacity-75">
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    
                    {message.isVoice && (
                      <Volume2 className="w-3 h-3" />
                    )}
                    
                    {message.language && message.language !== 'en' && (
                      <LanguageBadge language={message.language} />
                    )}
                    
                    {message.action && (
                      <div className="flex items-center space-x-1">
                        <CheckCircle className="w-3 h-3" />
                        <span>{message.action}</span>
                      </div>
                    )}
                  </div>

                  {}
                  {message.type === 'agent' && message.performance && (
                    <div className="mt-1 text-xs opacity-75">
                      <span className={getPerformanceColor(message.performance.total_duration_ms)}>
                        Response time: {formatDuration(message.performance.total_duration_ms)}
                      </span>
                    </div>
                  )}

                  {}
                  {showPerformance && message.performance && (
                    <div className="mt-2 p-2 bg-black bg-opacity-10 rounded text-xs">
                      <div className="flex items-center justify-between">
                        <span>Total:</span>
                        <span className={getPerformanceColor(message.performance.total_duration_ms)}>
                          {formatDuration(message.performance.total_duration_ms)}
                        </span>
                      </div>
                      
                      {message.performance.component_timings && (
                        <div className="mt-1 space-y-1">
                          {Object.entries(message.performance.component_timings).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="capitalize">{key.replace('_ms', '').replace('_', ' ')}:</span>
                              <span>{formatDuration(value as number)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {message.performance.within_target_latency !== undefined && (
                        <div className="flex items-center justify-between mt-1">
                          <span>Target Met:</span>
                          <span className={message.performance.within_target_latency ? 'text-success-600' : 'text-error-600'}>
                            {message.performance.within_target_latency ? '✓' : '✗'}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {}
        {isLoading && (
          <ChatLoadingBubble type="thinking" />
        )}

        <div ref={messagesEndRef} />
      </div>

      {}
      {error && (
        <div className="mx-4 mb-4">
          <ErrorDisplay 
            error={error} 
            onDismiss={() => setError(null)}
          />
        </div>
      )}

      {}
      {voiceState.error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <MicOff className="w-5 h-5 text-red-600" />
            <span className="text-sm text-red-700">{voiceState.error}</span>
          </div>
        </div>
      )}

      {}
      {voiceState.isRecording && (
        <div className="mx-4 mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Mic className="w-4 h-4 text-red-600 animate-pulse" />
              <span className="text-sm font-medium text-blue-700">🎤 Recording...</span>
            </div>
            <span className="text-sm text-blue-600">
              {voiceState.duration.toFixed(1)}s
            </span>
          </div>
        </div>
      )}

      {}
      {isProcessingVoice && !voiceState.isRecording && (
        <div className="mx-4 mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 text-purple-600 animate-spin" />
            <span className="text-sm font-medium text-purple-700">Processing voice...</span>
          </div>
        </div>
      )}

      {}
      {voiceState.audioBlob && !voiceState.isRecording && (
        <div className="mx-4 mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Volume2 className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-700">
                Recording ready ({voiceState.duration.toFixed(1)}s)
              </span>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={voiceControls.clearRecording}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
              <button
                onClick={handleVoiceSubmit}
                disabled={isLoading}
                className="text-xs text-green-600 hover:text-green-700 font-medium"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}

      {}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleTextSubmit} className="flex items-end space-x-2">
          <div className="flex-1">
            <input
              ref={textInputRef}
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type your message or use voice..."
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
          </div>
          
          {}
          <button
            type="button"
            onClick={voiceState.isRecording ? voiceControls.stopRecording : voiceControls.startRecording}
            disabled={isLoading || !voiceState.isSupported}
            className={`p-2 rounded-lg transition-colors ${
              voiceState.isRecording
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={voiceState.isRecording ? 'Stop recording' : 'Start voice recording'}
          >
            {voiceState.isRecording ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>
          
          {}
          <button
            type="submit"
            disabled={!textInput.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center space-x-2">
            {!voiceState.isSupported && (
              <p className="text-xs text-gray-500">
                Voice recording is not supported in this browser
              </p>
            )}
            {voiceState.isSupported && selectedLanguage !== 'auto' && (
              <p className="text-xs text-gray-500">
                Language: {selectedLanguage === 'en' ? 'English' : selectedLanguage === 'hi' ? 'Hindi' : 'Tamil'}
              </p>
            )}
          </div>
          {selectedLanguage === 'auto' && (
            <p className="text-xs text-gray-400">
              Auto-detecting language
            </p>
          )}
        </div>
      </div>
    </div>
  );
};