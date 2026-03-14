import { AxiosError } from 'axios';

export interface ParsedError {
  title: string;
  message: string;
  type: 'network' | 'server' | 'validation' | 'not_found' | 'conflict' | 'unknown';
  details?: string;
}


export const parseApiError = (error: unknown): ParsedError => {

  if (error instanceof Error && error.message === 'Network Error') {
    return {
      title: 'Connection Error',
      message: 'Unable to connect to the server. Please check your internet connection.',
      type: 'network',
    };
  }

  // Axios errors with response
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as AxiosError<any>;
    const status = axiosError.response?.status;
    const data = axiosError.response?.data;


    const errorMessage = 
      data?.detail || 
      data?.message || 
      data?.error || 
      (typeof data === 'string' ? data : null);

    switch (status) {
      case 400:
        return {
          title: 'Invalid Request',
          message: errorMessage || 'The request contains invalid data.',
          type: 'validation',
          details: data?.errors ? JSON.stringify(data.errors) : undefined,
        };

      case 404:

        if (errorMessage?.toLowerCase().includes('doctor')) {
          return {
            title: 'Doctor Not Found',
            message: 'The requested doctor does not exist. Please check the doctor name or ID.',
            type: 'not_found',
          };
        }
        if (errorMessage?.toLowerCase().includes('patient')) {
          return {
            title: 'Patient Not Found',
            message: 'The patient ID does not exist. Please verify the patient information.',
            type: 'not_found',
          };
        }
        if (errorMessage?.toLowerCase().includes('appointment')) {
          return {
            title: 'Appointment Not Found',
            message: 'The requested appointment does not exist or has been cancelled.',
            type: 'not_found',
          };
        }
        return {
          title: 'Not Found',
          message: errorMessage || 'The requested resource was not found.',
          type: 'not_found',
        };

      case 409:

        if (errorMessage?.toLowerCase().includes('conflict') || 
            errorMessage?.toLowerCase().includes('already exists')) {
          return {
            title: 'Appointment Conflict',
            message: errorMessage || 'An appointment already exists at this time. Please choose a different time slot.',
            type: 'conflict',
          };
        }
        return {
          title: 'Conflict',
          message: errorMessage || 'The operation conflicts with existing data.',
          type: 'conflict',
        };

      case 422:
        return {
          title: 'Validation Error',
          message: errorMessage || 'The provided data is invalid or incomplete.',
          type: 'validation',
          details: data?.errors ? JSON.stringify(data.errors) : undefined,
        };

      case 500:
      case 502:
      case 503:
        return {
          title: 'Server Error',
          message: 'The server encountered an error. Please try again later.',
          type: 'server',
          details: errorMessage,
        };

      case 504:
        return {
          title: 'Timeout',
          message: 'The request took too long to process. Please try again.',
          type: 'server',
        };

      default:
        return {
          title: 'Error',
          message: errorMessage || 'An unexpected error occurred.',
          type: 'unknown',
          details: status ? `Status: ${status}` : undefined,
        };
    }
  }

  // Timeout errors
  if (error instanceof Error && error.message.includes('timeout')) {
    return {
      title: 'Request Timeout',
      message: 'The request took too long to complete. Please try again.',
      type: 'server',
    };
  }

  // Generic errors
  if (error instanceof Error) {
    return {
      title: 'Error',
      message: error.message,
      type: 'unknown',
    };
  }

  // Unknown error type
  return {
    title: 'Unknown Error',
    message: 'An unexpected error occurred. Please try again.',
    type: 'unknown',
  };
};


export const getErrorIcon = (type: ParsedError['type']): string => {
  switch (type) {
    case 'network':
      return 'wifi-off';
    case 'not_found':
      return 'search-x';
    case 'conflict':
      return 'alert-triangle';
    case 'validation':
      return 'alert-circle';
    case 'server':
      return 'server-crash';
    default:
      return 'alert-circle';
  }
};


export const getErrorColor = (type: ParsedError['type']): string => {
  switch (type) {
    case 'network':
      return 'orange';
    case 'not_found':
      return 'blue';
    case 'conflict':
      return 'yellow';
    case 'validation':
      return 'red';
    case 'server':
      return 'red';
    default:
      return 'red';
  }
};
