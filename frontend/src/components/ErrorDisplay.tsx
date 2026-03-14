import React from 'react';
import { 
  AlertCircle, 
  WifiOff, 
  SearchX, 
  AlertTriangle, 
  ServerCrash,
  X 
} from 'lucide-react';
import { ParsedError } from '../utils/errorHandler';

interface ErrorDisplayProps {
  error: ParsedError;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ 
  error, 
  onDismiss,
  className = '' 
}) => {
  const getIcon = () => {
    switch (error.type) {
      case 'network':
        return <WifiOff className="w-5 h-5" />;
      case 'not_found':
        return <SearchX className="w-5 h-5" />;
      case 'conflict':
        return <AlertTriangle className="w-5 h-5" />;
      case 'server':
        return <ServerCrash className="w-5 h-5" />;
      default:
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  const getColorClasses = () => {
    switch (error.type) {
      case 'network':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          text: 'text-orange-700',
          icon: 'text-orange-600',
        };
      case 'not_found':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          icon: 'text-blue-600',
        };
      case 'conflict':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          icon: 'text-yellow-600',
        };
      default:
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          icon: 'text-red-600',
        };
    }
  };

  const colors = getColorClasses();

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        <div className={`${colors.icon} flex-shrink-0 mt-0.5`}>
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-semibold ${colors.text}`}>
            {error.title}
          </h3>
          <p className={`text-sm mt-1 ${colors.text}`}>
            {error.message}
          </p>
          
          {error.details && (
            <details className="mt-2">
              <summary className={`text-xs ${colors.text} cursor-pointer hover:underline`}>
                Technical details
              </summary>
              <pre className={`text-xs mt-1 ${colors.text} opacity-75 overflow-x-auto`}>
                {error.details}
              </pre>
            </details>
          )}
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className={`${colors.icon} hover:opacity-75 flex-shrink-0`}
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

interface InlineErrorProps {
  message: string;
  type?: 'error' | 'warning' | 'info';
}

export const InlineError: React.FC<InlineErrorProps> = ({ 
  message, 
  type = 'error' 
}) => {
  const getColorClasses = () => {
    switch (type) {
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          icon: 'text-yellow-600',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          icon: 'text-blue-600',
        };
      default:
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          icon: 'text-red-600',
        };
    }
  };

  const colors = getColorClasses();

  return (
    <div className={`${colors.bg} ${colors.border} border rounded px-3 py-2 flex items-center space-x-2`}>
      <AlertCircle className={`w-4 h-4 ${colors.icon} flex-shrink-0`} />
      <span className={`text-sm ${colors.text}`}>{message}</span>
    </div>
  );
};
