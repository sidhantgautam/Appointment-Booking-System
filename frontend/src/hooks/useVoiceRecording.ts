import { useState, useRef, useCallback } from 'react';

export interface VoiceRecordingState {
  isRecording: boolean;
  isSupported: boolean;
  audioBlob: Blob | null;
  duration: number;
  error: string | null;
}

export interface VoiceRecordingControls {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  clearRecording: () => void;
}

export const useVoiceRecording = (): [VoiceRecordingState, VoiceRecordingControls] => {
  const [state, setState] = useState<VoiceRecordingState>({
    isRecording: false,
    isSupported: typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
    audioBlob: null,
    duration: 0,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = useCallback(async () => {
    if (!state.isSupported) {
      setState(prev => ({ ...prev, error: 'Voice recording is not supported in this browser' }));
      return;
    }

    try {
      // Clear previous recording
      chunksRef.current = [];
      setState(prev => ({ ...prev, error: null, audioBlob: null, duration: 0 }));

      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        } 
      });
      
      streamRef.current = stream;

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      });
      
      mediaRecorderRef.current = mediaRecorder;

      // Set up event handlers
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { 
          type: mediaRecorder.mimeType 
        });
        
        setState(prev => ({ 
          ...prev, 
          isRecording: false, 
          audioBlob 
        }));

        // Clean up
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setState(prev => ({ 
          ...prev, 
          error: 'Recording failed. Please try again.',
          isRecording: false 
        }));
      };

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      startTimeRef.current = Date.now();
      
      setState(prev => ({ ...prev, isRecording: true }));

      // Start duration timer
      durationIntervalRef.current = setInterval(() => {
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        setState(prev => ({ ...prev, duration: elapsed }));
      }, 100);

    } catch (error) {
      console.error('Error starting recording:', error);
      let errorMessage = 'Failed to start recording. ';
      
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError') {
          errorMessage += 'Microphone access denied. Please allow microphone access and try again.';
        } else if (error.name === 'NotFoundError') {
          errorMessage += 'No microphone found. Please connect a microphone and try again.';
        } else {
          errorMessage += error.message;
        }
      }
      
      setState(prev => ({ ...prev, error: errorMessage, isRecording: false }));
    }
  }, [state.isSupported]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop();
    }
  }, [state.isRecording]);

  const clearRecording = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      audioBlob: null, 
      duration: 0, 
      error: null 
    }));
    chunksRef.current = [];
  }, []);

  return [
    state,
    {
      startRecording,
      stopRecording,
      clearRecording,
    }
  ];
};


export const blobToFile = (blob: Blob, filename: string = 'recording.webm'): File => {
  return new File([blob], filename, { type: blob.type });
};


export const getAudioDuration = (blob: Blob): Promise<number> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio();
    const url = URL.createObjectURL(blob);
    
    audio.addEventListener('loadedmetadata', () => {
      URL.revokeObjectURL(url);
      resolve(audio.duration);
    });
    
    audio.addEventListener('error', () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load audio'));
    });
    
    audio.src = url;
  });
};