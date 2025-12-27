import React, { useState, useEffect } from 'react';
import AgriculturalDroneDashboard from './AgriculturalDroneDashboard';
import CropHealthMonitor from './CropHealthMonitor';
import FarmScanner from './FarmScanner';
import { Plane, Leaf, Map, Settings as SettingsIcon, Moon, Sun, Globe } from 'lucide-react';
import { translations, getTranslation } from './translations';

function App() {
  const [activeView, setActiveView] = useState('scanner'); // drone, health, or scanner
  const [showSettings, setShowSettings] = useState(false);

  // Load settings from localStorage or use defaults
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'en';
  });

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    localStorage.setItem('language', language);
  }, [darkMode, language]);

  const t = (key) => getTranslation(language, key);

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'ru', name: 'Русский', flag: '🇷🇺' },
    { code: 'fa', name: 'فارسی', flag: '🇮🇷' },
    { code: 'es', name: 'Español', flag: '🇪🇸' }
  ];

  const bgClass = darkMode ? 'bg-gray-900' : 'bg-gray-50';
  const navBgClass = darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-green-500';
  const textClass = darkMode ? 'text-gray-100' : 'text-gray-800';
  const cardBgClass = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <div className={`min-h-screen ${bgClass} ${textClass} transition-colors duration-200`}>
      {/* Top Navigation Bar */}
      <nav className={`${navBgClass} shadow-md border-b-2 sticky top-0 z-50 transition-colors duration-200`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <Plane className="w-8 h-8 text-green-600" />
              <h1 className={`text-2xl font-bold ${textClass}`}>{t('appName')}</h1>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveView('drone')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'drone'
                    ? 'bg-blue-500 text-white shadow-lg'
                    : darkMode
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Plane className="w-4 h-4" />
                <span className="hidden sm:inline">{t('droneControl')}</span>
              </button>

              <button
                onClick={() => setActiveView('health')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'health'
                    ? 'bg-green-500 text-white shadow-lg'
                    : darkMode
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Leaf className="w-4 h-4" />
                <span className="hidden sm:inline">{t('cropHealth')}</span>
              </button>

              <button
                onClick={() => setActiveView('scanner')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'scanner'
                    ? 'bg-purple-500 text-white shadow-lg'
                    : darkMode
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Map className="w-4 h-4" />
                <span className="hidden sm:inline">{t('farmScanner')}</span>
              </button>

              {/* Settings Button */}
              <button
                onClick={() => setShowSettings(!showSettings)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ml-2 ${
                  showSettings
                    ? 'bg-gray-500 text-white shadow-lg'
                    : darkMode
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <SettingsIcon className="w-4 h-4" />
                <span className="hidden sm:inline">{t('settings')}</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Settings Panel */}
      {showSettings && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className={`${cardBgClass} rounded-xl shadow-2xl max-w-md w-full p-6 ${textClass}`}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <SettingsIcon className="w-6 h-6 text-blue-500" />
                {t('settingsTitle')}
              </h2>
              <button
                onClick={() => setShowSettings(false)}
                className={`p-2 rounded-lg ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
              >
                ✕
              </button>
            </div>

            {/* Dark Mode Toggle */}
            <div className="mb-6">
              <label className="flex items-center justify-between p-4 rounded-lg border border-gray-300 dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <div className="flex items-center gap-3">
                  {darkMode ? <Moon className="w-5 h-5 text-blue-500" /> : <Sun className="w-5 h-5 text-yellow-500" />}
                  <span className="font-medium">{t('darkMode')}</span>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={darkMode}
                    onChange={(e) => setDarkMode(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-12 h-6 rounded-full transition-colors ${darkMode ? 'bg-blue-500' : 'bg-gray-300'}`}>
                    <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${darkMode ? 'translate-x-6' : 'translate-x-1'} mt-0.5`}></div>
                  </div>
                </div>
              </label>
            </div>

            {/* Language Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-3 flex items-center gap-2">
                <Globe className="w-5 h-5 text-green-500" />
                {t('language')}
              </label>
              <div className="space-y-2">
                {languages.map(lang => (
                  <button
                    key={lang.code}
                    onClick={() => setLanguage(lang.code)}
                    className={`w-full p-3 rounded-lg flex items-center gap-3 transition-all ${
                      language === lang.code
                        ? 'bg-green-500 text-white shadow-lg'
                        : darkMode
                        ? 'bg-gray-700 hover:bg-gray-600'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    <span className="text-2xl">{lang.flag}</span>
                    <span className="font-medium">{lang.name}</span>
                    {language === lang.code && (
                      <span className="ml-auto">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={() => setShowSettings(false)}
              className="w-full py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              {t('closeSettings')}
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div>
        {activeView === 'drone' && <AgriculturalDroneDashboard darkMode={darkMode} language={language} t={t} />}
        {activeView === 'health' && <CropHealthMonitor darkMode={darkMode} language={language} t={t} />}
        {activeView === 'scanner' && <FarmScanner darkMode={darkMode} language={language} t={t} />}
      </div>
    </div>
  );
}

export default App;
