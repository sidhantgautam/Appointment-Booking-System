import React from 'react';
import { 
  Stethoscope, 
  Languages, 
  List, 
  X,
  Zap
} from 'lucide-react';

interface QuickTestButtonsProps {
  onTestAction: (message: string, description: string) => void;
  disabled?: boolean;
}

const testActions = [
  {
    id: 'book-cardiology',
    label: 'Book Cardiology',
    message: 'Book appointment with Dr Sharma tomorrow at 11 AM for patient 1',
    description: 'Book cardiology appointment',
    icon: Stethoscope,
    color: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
  },
  {
    id: 'book-hindi',
    label: 'Hindi Booking',
    message: 'कल सुबह 10 बजे डॉ शर्मा के साथ अपॉइंटमेंट बुक करें patient 1',
    description: 'Book appointment in Hindi',
    icon: Languages,
    color: 'bg-orange-100 text-orange-700 hover:bg-orange-200',
  },
  {
    id: 'book-tamil',
    label: 'Tamil Booking',
    message: 'நாளை காலை 10 மணிக்கு டாக்டர் ஷர்மாவுடன் அப்பாயின்ட்மென்ட் patient 1',
    description: 'Book appointment in Tamil',
    icon: Languages,
    color: 'bg-green-100 text-green-700 hover:bg-green-200',
  },
  {
    id: 'view-appointments',
    label: 'View Appointments',
    message: 'Show my appointments for patient 1',
    description: 'List all appointments',
    icon: List,
    color: 'bg-purple-100 text-purple-700 hover:bg-purple-200',
  },
  {
    id: 'cancel-appointment',
    label: 'Cancel Appointment',
    message: 'Cancel my appointment with Dr Sharma tomorrow for patient 1',
    description: 'Cancel an appointment',
    icon: X,
    color: 'bg-red-100 text-red-700 hover:bg-red-200',
  },
];

export const QuickTestButtons: React.FC<QuickTestButtonsProps> = ({ 
  onTestAction, 
  disabled = false 
}) => {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
      <div className="flex items-center space-x-2 mb-3">
        <Zap className="w-5 h-5 text-blue-600" />
        <h3 className="text-sm font-semibold text-gray-900">Quick Test Actions</h3>
        <span className="text-xs text-gray-500">(Demo Mode)</span>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
        {testActions.map((action) => (
          <button
            key={action.id}
            onClick={() => onTestAction(action.message, action.description)}
            disabled={disabled}
            className={`flex flex-col items-center justify-center p-3 rounded-lg transition-all ${action.color} disabled:opacity-50 disabled:cursor-not-allowed`}
            title={action.description}
          >
            <action.icon className="w-5 h-5 mb-1" />
            <span className="text-xs font-medium text-center">{action.label}</span>
          </button>
        ))}
      </div>
      
      <p className="text-xs text-gray-600 mt-3">
        Click any button to quickly test the system with predefined requests
      </p>
    </div>
  );
};


export const QuickTestButtonsCompact: React.FC<QuickTestButtonsProps> = ({ 
  onTestAction, 
  disabled = false 
}) => {
  return (
    <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
      <div className="flex items-center space-x-2 mb-2">
        <Zap className="w-4 h-4 text-blue-600" />
        <h4 className="text-xs font-semibold text-gray-900">Quick Tests</h4>
      </div>
      
      <div className="flex flex-wrap gap-1.5">
        {testActions.map((action) => (
          <button
            key={action.id}
            onClick={() => onTestAction(action.message, action.description)}
            disabled={disabled}
            className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium transition-all ${action.color} disabled:opacity-50 disabled:cursor-not-allowed`}
            title={action.description}
          >
            <action.icon className="w-3 h-3" />
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};