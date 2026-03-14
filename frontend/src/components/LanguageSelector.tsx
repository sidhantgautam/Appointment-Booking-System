import React from 'react';
import { Languages, Globe } from 'lucide-react';

export type LanguageOption = 'auto' | 'en' | 'hi' | 'ta';

interface LanguageSelectorProps {
  selectedLanguage: LanguageOption;
  onLanguageChange: (language: LanguageOption) => void;
  className?: string;
}

const languageOptions = [
  { value: 'auto' as LanguageOption, label: 'Auto Detect', icon: Globe, flag: '🌐' },
  { value: 'en' as LanguageOption, label: 'English', icon: Languages, flag: '🇬🇧' },
  { value: 'hi' as LanguageOption, label: 'हिंदी (Hindi)', icon: Languages, flag: '🇮🇳' },
  { value: 'ta' as LanguageOption, label: 'தமிழ் (Tamil)', icon: Languages, flag: '🇮🇳' },
];

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  selectedLanguage,
  onLanguageChange,
  className = '',
}) => {
  const selectedOption = languageOptions.find(opt => opt.value === selectedLanguage);

  return (
    <div className={`relative inline-block ${className}`}>
      <label htmlFor="language-select" className="sr-only">
        Select Language
      </label>
      <div className="relative">
        <select
          id="language-select"
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value as LanguageOption)}
          className="appearance-none bg-white border border-gray-300 rounded-lg pl-10 pr-8 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer hover:bg-gray-50 transition-colors"
        >
          {languageOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.flag} {option.label}
            </option>
          ))}
        </select>
        
        {}
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
          {selectedOption?.icon && (
            <selectedOption.icon className="w-4 h-4 text-gray-500" />
          )}
        </div>
        
        {}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {}
      {selectedLanguage === 'auto' && (
        <p className="text-xs text-gray-500 mt-1">
          Language will be detected automatically
        </p>
      )}
    </div>
  );
};


export const LanguageSelectorCompact: React.FC<LanguageSelectorProps> = ({
  selectedLanguage,
  onLanguageChange,
  className = '',
}) => {
  return (
    <div className={`relative inline-block ${className}`}>
      <select
        value={selectedLanguage}
        onChange={(e) => onLanguageChange(e.target.value as LanguageOption)}
        className="appearance-none bg-gray-100 hover:bg-gray-200 border-0 rounded-lg pl-8 pr-6 py-1.5 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-colors"
        title="Select language"
      >
        {languageOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.flag} {option.label}
          </option>
        ))}
      </select>
      
      <div className="absolute left-2 top-1/2 transform -translate-y-1/2 pointer-events-none">
        <Languages className="w-3.5 h-3.5 text-gray-600" />
      </div>
      
      <div className="absolute right-1.5 top-1/2 transform -translate-y-1/2 pointer-events-none">
        <svg className="w-3 h-3 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
};


interface LanguageBadgeProps {
  language: string;
  className?: string;
}

export const LanguageBadge: React.FC<LanguageBadgeProps> = ({ language, className = '' }) => {
  const getLanguageInfo = (lang: string) => {
    switch (lang.toLowerCase()) {
      case 'en':
      case 'english':
        return { label: 'English', flag: '🇬🇧', color: 'bg-blue-100 text-blue-800' };
      case 'hi':
      case 'hindi':
        return { label: 'Hindi', flag: '🇮🇳', color: 'bg-orange-100 text-orange-800' };
      case 'ta':
      case 'tamil':
        return { label: 'Tamil', flag: '🇮🇳', color: 'bg-green-100 text-green-800' };
      default:
        return { label: language, flag: '🌐', color: 'bg-gray-100 text-gray-800' };
    }
  };

  const info = getLanguageInfo(language);

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${info.color} ${className}`}>
      <span className="mr-1">{info.flag}</span>
      {info.label}
    </span>
  );
};