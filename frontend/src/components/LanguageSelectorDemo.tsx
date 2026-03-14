import React, { useState } from 'react';
import { LanguageSelector, LanguageSelectorCompact, LanguageBadge, LanguageOption } from './LanguageSelector';
import { MessageCircle } from 'lucide-react';

export const LanguageSelectorDemo: React.FC = () => {
  const [language, setLanguage] = useState<LanguageOption>('auto');
  const [compactLanguage, setCompactLanguage] = useState<LanguageOption>('en');

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Language Selector Components</h1>
        <p className="text-gray-600">Interactive demo of language selection components</p>
      </div>

      {}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Full Language Selector</h2>
        <p className="text-gray-600 mb-4">
          Use this in settings or prominent areas where language selection is important.
        </p>
        
        <LanguageSelector
          selectedLanguage={language}
          onLanguageChange={setLanguage}
        />
        
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">
            <strong>Selected:</strong> {language}
          </p>
        </div>
      </div>

      {}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Compact Language Selector</h2>
        <p className="text-gray-600 mb-4">
          Use this in headers, toolbars, or space-constrained areas.
        </p>
        
        <div className="flex items-center space-x-4">
          <MessageCircle className="w-6 h-6 text-blue-600" />
          <span className="text-lg font-medium">Voice AI Assistant</span>
          <LanguageSelectorCompact
            selectedLanguage={compactLanguage}
            onLanguageChange={setCompactLanguage}
          />
        </div>
        
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">
            <strong>Selected:</strong> {compactLanguage}
          </p>
        </div>
      </div>

      {}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Language Badges</h2>
        <p className="text-gray-600 mb-4">
          Use these to display detected or active languages in messages.
        </p>
        
        <div className="flex flex-wrap gap-3">
          <LanguageBadge language="en" />
          <LanguageBadge language="hi" />
          <LanguageBadge language="ta" />
          <LanguageBadge language="English" />
          <LanguageBadge language="Hindi" />
          <LanguageBadge language="Tamil" />
        </div>
      </div>

      {}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage in Conversation</h2>
        <p className="text-gray-600 mb-4">
          Example of how language badges appear in chat messages.
        </p>
        
        <div className="space-y-4">
          {}
          <div className="flex justify-end">
            <div className="bg-blue-600 text-white px-4 py-2 rounded-lg max-w-xs">
              <p className="text-sm">नमस्ते, मुझे कल के लिए अपॉइंटमेंट बुक करना है</p>
              <div className="flex items-center space-x-2 mt-1 text-xs opacity-75">
                <span>2:30 PM</span>
                <LanguageBadge language="hi" className="bg-blue-500 text-white" />
              </div>
            </div>
          </div>

          {}
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg max-w-xs">
              <p className="text-sm">आप किस डॉक्टर के साथ अपॉइंटमेंट बुक करना चाहेंगे?</p>
              <div className="flex items-center space-x-2 mt-1 text-xs opacity-75">
                <span>2:30 PM</span>
                <LanguageBadge language="hi" />
              </div>
            </div>
          </div>

          {}
          <div className="flex justify-end">
            <div className="bg-blue-600 text-white px-4 py-2 rounded-lg max-w-xs">
              <p className="text-sm">நாளை காலை 10 மணிக்கு அப்பாயின்ட்மென்ட் வேண்டும்</p>
              <div className="flex items-center space-x-2 mt-1 text-xs opacity-75">
                <span>2:31 PM</span>
                <LanguageBadge language="ta" className="bg-blue-500 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Integration Guide</h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p><strong>Import:</strong></p>
          <code className="block bg-white p-2 rounded text-xs">
            import {'{ LanguageSelector, LanguageSelectorCompact, LanguageBadge }'} from './LanguageSelector';
          </code>
          
          <p className="mt-4"><strong>Usage:</strong></p>
          <code className="block bg-white p-2 rounded text-xs">
            const [language, setLanguage] = useState&lt;LanguageOption&gt;('auto');<br/>
            &lt;LanguageSelector selectedLanguage={'{language}'} onLanguageChange={'{setLanguage}'} /&gt;
          </code>
          
          <p className="mt-4"><strong>Language Options:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>'auto' - Auto-detect language</li>
            <li>'en' - English</li>
            <li>'hi' - Hindi (हिंदी)</li>
            <li>'ta' - Tamil (தமிழ்)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};