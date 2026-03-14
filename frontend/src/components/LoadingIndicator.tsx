import React from 'react';
import { Loader2, Mic, MessageCircle, Brain } from 'lucide-react';

interface LoadingIndicatorProps {
  message?: string;
  type?: 'default' | 'voice' | 'thinking' | 'processing';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ 
  message,
  type = 'default',
  size = 'md',
  className = '' 
}) => {
  const getIcon = () => {
    switch (type) {
      case 'voice':
        return <Mic className={`${getSizeClass()} animate-pulse`} />;
      case 'thinking':
        return <Brain className={`${getSizeClass()} animate-pulse`} />;
      case 'processing':
        return <MessageCircle className={`${getSizeClass()} animate-pulse`} />;
      default:
        return <Loader2 className={`${getSizeClass()} animate-spin`} />;
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'w-4 h-4';
      case 'lg':
        return 'w-8 h-8';
      default:
        return 'w-5 h-5';
    }
  };

  const getMessage = () => {
    if (message) return message;
    
    switch (type) {
      case 'voice':
        return 'Processing voice...';
      case 'thinking':
        return 'Thinking...';
      case 'processing':
        return 'Processing...';
      default:
        return 'Loading...';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="text-blue-600">
        {getIcon()}
      </div>
      <span className="text-sm text-gray-600">{getMessage()}</span>
    </div>
  );
};

interface ChatLoadingBubbleProps {
  type?: 'voice' | 'thinking' | 'processing';
}

export const ChatLoadingBubble: React.FC<ChatLoadingBubbleProps> = ({ 
  type = 'thinking' 
}) => {
  const getMessage = () => {
    switch (type) {
      case 'voice':
        return 'Transcribing audio...';
      case 'processing':
        return 'Processing your request...';
      default:
        return 'Thinking...';
    }
  };

  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-xs">
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-sm text-gray-600">{getMessage()}</span>
        </div>
      </div>
    </div>
  );
};

interface FullPageLoadingProps {
  message?: string;
}

export const FullPageLoading: React.FC<FullPageLoadingProps> = ({ 
  message = 'Loading...' 
}) => {
  return (
    <div className="flex items-center justify-center h-full min-h-[400px]">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
};

interface ButtonLoadingProps {
  isLoading: boolean;
  children: React.ReactNode;
  loadingText?: string;
}

export const ButtonLoading: React.FC<ButtonLoadingProps> = ({ 
  isLoading, 
  children,
  loadingText 
}) => {
  if (!isLoading) {
    return <>{children}</>;
  }

  return (
    <div className="flex items-center space-x-2">
      <Loader2 className="w-4 h-4 animate-spin" />
      {loadingText && <span>{loadingText}</span>}
    </div>
  );
};
