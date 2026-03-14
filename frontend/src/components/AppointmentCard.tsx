import React from 'react';
import { Calendar, Clock, Stethoscope } from 'lucide-react';

interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  doctor_name: string;
  specialization: string;
  time: string;
}

interface AppointmentCardProps {
  appointment: Appointment;
  compact?: boolean;
}

export const AppointmentCard: React.FC<AppointmentCardProps> = ({ 
  appointment, 
  compact = false 
}) => {
  const formatDateTime = (timeStr: string): { date: string; time: string } | null => {
    if (!timeStr || timeStr === 'null' || timeStr === 'None') {
      return null;
    }

    try {
      // Try parsing as ISO date
      const date = new Date(timeStr);
      if (!isNaN(date.getTime())) {
        return {
          date: date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          }),
          time: date.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
          })
        };
      }



      const dateMatch = timeStr.match(/(\w+ \d+, \d+) at (\d+:\d+ [AP]M)/i);
      if (dateMatch) {
        return {
          date: dateMatch[1],
          time: dateMatch[2]
        };
      }


      return {
        date: timeStr,
        time: ''
      };
    } catch (error) {
      return {
        date: timeStr,
        time: ''
      };
    }
  };

  const dateTime = formatDateTime(appointment.time);

  if (!dateTime) {
    return null;
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2 text-sm py-1">
        <Calendar className="w-3 h-3 text-gray-400 flex-shrink-0" />
        <span className="text-gray-700">{dateTime.date}</span>
        {dateTime.time && (
          <>
            <Clock className="w-3 h-3 text-gray-400 flex-shrink-0" />
            <span className="text-gray-700">{dateTime.time}</span>
          </>
        )}
        <span className="text-gray-400">•</span>
        <Stethoscope className="w-3 h-3 text-blue-500 flex-shrink-0" />
        <span className="text-gray-900 font-medium">Dr {appointment.doctor_name}</span>
        <span className="text-gray-500">({appointment.specialization})</span>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="flex items-center space-x-2">
            <Stethoscope className="w-4 h-4 text-blue-600" />
            <span className="font-semibold text-gray-900">Dr {appointment.doctor_name}</span>
            <span className="text-sm text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              {appointment.specialization}
            </span>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>{dateTime.date}</span>
            </div>
            {dateTime.time && (
              <div className="flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5" />
                <span>{dateTime.time}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface AppointmentListProps {
  appointments: Appointment[];
  message?: string;
  compact?: boolean;
}

export const AppointmentList: React.FC<AppointmentListProps> = ({ 
  appointments, 
  message,
  compact = true 
}) => {

  const validAppointments = appointments.filter(appt => {
    return appt.time && appt.time !== 'null' && appt.time !== 'None';
  });

  if (validAppointments.length === 0) {
    return (
      <div className="text-gray-600">
        {message || 'No appointments found.'}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {message && (
        <div className="text-gray-900 font-medium mb-2">{message}</div>
      )}
      <div className={compact ? 'space-y-1' : 'space-y-2'}>
        {validAppointments.map((appointment) => (
          <AppointmentCard 
            key={appointment.id} 
            appointment={appointment} 
            compact={compact}
          />
        ))}
      </div>
    </div>
  );
};

interface DoctorListProps {
  doctors: Array<{ id: number; name: string; specialization: string }>;
  message?: string;
}

export const DoctorList: React.FC<DoctorListProps> = ({ doctors, message }) => {
  if (doctors.length === 0) {
    return (
      <div className="text-gray-600">
        {message || 'No doctors found.'}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {message && (
        <div className="text-gray-900 font-medium mb-2">{message}</div>
      )}
      <div className="space-y-1">
        {doctors.map((doctor) => (
          <div key={doctor.id} className="flex items-center space-x-2 text-sm py-1">
            <Stethoscope className="w-3 h-3 text-blue-500 flex-shrink-0" />
            <span className="text-gray-900 font-medium">Dr {doctor.name}</span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-600">{doctor.specialization}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface FormattedListProps {
  items: string[];
  message?: string;
}

export const FormattedList: React.FC<FormattedListProps> = ({ items, message }) => {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {message && (
        <div className="text-gray-900 font-medium mb-2">{message}</div>
      )}
      <div className="space-y-1">
        {items.map((item, index) => (
          <div key={index} className="flex items-start space-x-2 text-sm">
            <span className="text-gray-400 mt-0.5">•</span>
            <span className="text-gray-700">{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
