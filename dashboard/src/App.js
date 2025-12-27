import React, { useState } from 'react';
import AgriculturalDroneDashboard from './AgriculturalDroneDashboard';
import CropHealthMonitor from './CropHealthMonitor';
import FarmScanner from './FarmScanner';
import { Plane, Leaf, Map } from 'lucide-react';

function App() {
  const [activeView, setActiveView] = useState('drone'); // drone, health, or scanner

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="bg-white shadow-md border-b-2 border-green-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Plane className="w-8 h-8 text-green-600" />
              <h1 className="text-2xl font-bold text-gray-800">AgriVision Pro</h1>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setActiveView('drone')}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'drone'
                    ? 'bg-blue-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Plane className="w-5 h-5" />
                Drone Control
              </button>

              <button
                onClick={() => setActiveView('health')}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'health'
                    ? 'bg-green-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Leaf className="w-5 h-5" />
                Crop Health
              </button>

              <button
                onClick={() => setActiveView('scanner')}
                className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${
                  activeView === 'scanner'
                    ? 'bg-purple-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Map className="w-5 h-5" />
                Farm Scanner
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div>
        {activeView === 'drone' && <AgriculturalDroneDashboard />}
        {activeView === 'health' && <CropHealthMonitor />}
        {activeView === 'scanner' && <FarmScanner />}
      </div>
    </div>
  );
}

export default App;
