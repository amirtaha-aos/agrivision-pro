// src/AgriculturalDroneDashboard.jsx

import React, { useState, useEffect } from 'react';
import {
  Sprout,
  Battery,
  Satellite,
  Navigation,
  MapPin,
  Plane,
  TrendingUp,
  Leaf,
  Settings,
  Radio,
  AlertCircle,
  CheckCircle2,
  Moon,
  Sun,
  Camera,
} from 'lucide-react';

import { mavlinkAPI } from './api/mavlink';
import { imageAPI } from './api/imageProcessor';
import { API_CONFIG } from './api/config';

// === Tree growth database for mission config (height in meters, age in years) ===
const TREE_GROWTH_DB = {
  Oak: { maxHeight: 25, maturityAge: 20 },
  Pine: { maxHeight: 30, maturityAge: 15 },
  Maple: { maxHeight: 22, maturityAge: 18 },
  Birch: { maxHeight: 18, maturityAge: 12 },
  Willow: { maxHeight: 20, maturityAge: 10 },
  Cedar: { maxHeight: 35, maturityAge: 20 },
  Spruce: { maxHeight: 28, maturityAge: 18 },
  Elm: { maxHeight: 24, maturityAge: 16 },
  Ash: { maxHeight: 23, maturityAge: 17 },
  Poplar: { maxHeight: 26, maturityAge: 8 },
  Cherry: { maxHeight: 12, maturityAge: 10 },
  Apple: { maxHeight: 8, maturityAge: 8 },
  Walnut: { maxHeight: 20, maturityAge: 15 },
  Beech: { maxHeight: 25, maturityAge: 20 },
  Cypress: { maxHeight: 30, maturityAge: 20 },
  Sequoia: { maxHeight: 80, maturityAge: 50 },
  Redwood: { maxHeight: 90, maturityAge: 60 },
  Fir: { maxHeight: 32, maturityAge: 18 },
  Magnolia: { maxHeight: 15, maturityAge: 12 },
  Sycamore: { maxHeight: 27, maturityAge: 15 },
};

// Estimate tree height in meters based on age and species
const estimateTreeHeight = (species, ageYears) => {
  const plant = TREE_GROWTH_DB[species];
  if (!plant || !ageYears || ageYears <= 0) return null;

  const { maxHeight, maturityAge } = plant;
  const age = Number(ageYears);
  if (Number.isNaN(age) || age <= 0) return null;

  let estimatedHeight;

  if (age <= maturityAge) {
    // Growing phase – sigmoid-like growth
    const growthProgress = age / maturityAge;
    estimatedHeight = maxHeight * (1 - Math.exp(-3 * growthProgress));
  } else {
    // Mature phase – asymptotic growth slightly above maxHeight
    const yearsOverMaturity = age - maturityAge;
    const additionalGrowth = maxHeight * 0.15 * (1 - Math.exp(-0.1 * yearsOverMaturity));
    estimatedHeight = maxHeight + additionalGrowth;
  }

  // Small ±5% random variation
  const variation = (Math.random() - 0.5) * 0.1;
  estimatedHeight *= 1 + variation;

  return estimatedHeight;
};

// From canopy height to recommended flight altitude
const getRecommendedFlightAltitude = (canopyHeight) => {
  if (!canopyHeight) return null;
  // Canopy + 10m margin, clamped between 15m and 80m
  const raw = canopyHeight + 10;
  return Math.min(Math.max(raw, 15), 80);
};

const AgriculturalDroneDashboard = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [typewriterText, setTypewriterText] = useState('');
  const [showDashboard, setShowDashboard] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('mission'); // mission, telemetry, flight, analysis, camera

  // Mission config
  const [formData, setFormData] = useState({
    farmName: '',
    hectares: '',
    treeAge: '',
    treeType: '',
    terrainType: 'flat',
  });
  const [flightData, setFlightData] = useState(null);

  // Estimated tree height & recommended altitude
  const [estimatedTreeHeight, setEstimatedTreeHeight] = useState(null);
  const [recommendedAltitude, setRecommendedAltitude] = useState(null);

  // Connection & telemetry state
  const [isConnected, setIsConnected] = useState(false);
  const [telemetry, setTelemetry] = useState({
    gps: 'No Fix',
    satellites: 0,
    battery: 100,
    lat: 0,
    lon: 0,
    altitude: 0,
    speed: 0,
  });

  // Camera / image backend
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState('');

  // Analysis (YOLO / CV) state
  const [yoloStats, setYoloStats] = useState({
    healthy_count: 0,
    defective_count: 0,
    total_processed: 0,
  });
  const [healthOverview, setHealthOverview] = useState({
    score: null,
    status: '—',
  });

  // =========================
  // Splash typewriter
  // =========================
  useEffect(() => {
    const text = 'Modern Farming';
    let index = 0;
    const timer = setInterval(() => {
      if (index <= text.length) {
        setTypewriterText(text.slice(0, index));
        index++;
      } else {
        clearInterval(timer);
        setTimeout(() => {
          setShowSplash(false);
          setTimeout(() => setShowDashboard(true), 300);
        }, 1000);
      }
    }, 150);
    return () => clearInterval(timer);
  }, []);

  // =========================
  // Telemetry WebSocket (real backend data)
  // =========================
  useEffect(() => {
    if (!isConnected) return;

    const ws = new WebSocket(API_CONFIG.MAVLINK_WS);

    ws.onopen = () => {
      console.log('Telemetry WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Ignore error messages from backend
        if (data.error || data.connected === false) {
          return;
        }

        setTelemetry((prev) => ({
          ...prev,
          gps: data.gps_status || prev.gps,
          satellites: data.satellites ?? prev.satellites,
          battery: data.battery_percentage ?? prev.battery,
          lat: data.latitude ?? prev.lat,
          lon: data.longitude ?? prev.lon,
          altitude: data.altitude_relative ?? data.altitude ?? prev.altitude,
          speed: data.ground_speed ?? prev.speed,
        }));
      } catch (e) {
        console.error('Error parsing telemetry', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Telemetry WebSocket error', e);
    };

    ws.onclose = () => {
      console.log('Telemetry WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, [isConnected]);

  // =========================
  // Analysis WebSocket (YOLO + CV) – active while camera is on
  // =========================
  useEffect(() => {
    if (!isCameraOn) return;

    const ws = new WebSocket(API_CONFIG.ANALYSIS_WS);

    ws.onopen = () => {
      console.log('Analysis WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.yolo_stats) {
          setYoloStats(data.yolo_stats);
        }

        const results = data.results;
        if (results) {
          // Both YOLO and CV mode
          if (results.cv) {
            const cv = results.cv;
            if (typeof cv.overall_health_score === 'number') {
              setHealthOverview({
                score: cv.overall_health_score,
                status: cv.health_status || '—',
              });
            }
          } else if (results.overall_health_score) {
            // CV-only mode
            setHealthOverview({
              score: results.overall_health_score,
              status: results.health_status || '—',
            });
          }
        }
      } catch (e) {
        console.error('Error parsing analysis data', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Analysis WebSocket error', e);
    };

    ws.onclose = () => {
      console.log('Analysis WebSocket closed');
    };

    return () => {
      ws.close();
    };
  }, [isCameraOn]);

  // =========================
  // Auto-estimate tree height & recommended flight altitude
  // =========================
  useEffect(() => {
    const species = formData.treeType;
    const ageYears = parseFloat(formData.treeAge);

    if (!species || Number.isNaN(ageYears) || ageYears <= 0) {
      setEstimatedTreeHeight(null);
      setRecommendedAltitude(null);
      return;
    }

    if (!TREE_GROWTH_DB[species]) {
      setEstimatedTreeHeight(null);
      setRecommendedAltitude(null);
      return;
    }

    const height = estimateTreeHeight(species, ageYears);
    if (!height) {
      setEstimatedTreeHeight(null);
      setRecommendedAltitude(null);
      return;
    }

    const altitude = getRecommendedFlightAltitude(height);
    setEstimatedTreeHeight(height);
    setRecommendedAltitude(altitude);
  }, [formData.treeType, formData.treeAge]);

  // =========================
  // Mission: connect to MAVLink + calculate flight plan
  // =========================
  const handleStartMission = async () => {
    try {
      // 1) Check connection status
      let status;
      try {
        status = await mavlinkAPI.getStatus();
      } catch {
        status = { connected: false };
      }

      // 2) If not connected, connect to SITL on UDP
      if (!status.connected) {
        await mavlinkAPI.connect('udp:127.0.0.1:14550', 57600);
      }

      // 3) Ask backend to calculate mission plan
      const response = await mavlinkAPI.calculateMissionPlan(formData);
      if (response && response.plan) {
        setFlightData(response.plan);
        setIsConnected(true);
      } else {
        throw new Error('Invalid mission plan response');
      }
    } catch (error) {
      console.error('Failed to start mission:', error);
      alert('Error talking to Mission API (port 8000) or SITL. Check the backend terminal.');
    }
  };

  const handleDisconnect = async () => {
    try {
      await mavlinkAPI.disconnect();
    } catch (e) {
      console.warn('disconnect error (ignored):', e);
    }
    setIsConnected(false);
    setFlightData(null);
  };

  // =========================
  // Flight control buttons
  // =========================
  const handleArm = async () => {
    try {
      await mavlinkAPI.arm();
      alert('Drone armed.');
    } catch (e) {
      alert('Error while arming: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleTakeoff = async () => {
    try {
      const alt = flightData?.altitude || recommendedAltitude || 10;
      await mavlinkAPI.takeoff(alt);
      alert(`Takeoff command sent to ${alt} m.`);
    } catch (e) {
      alert('Error while takeoff: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleLand = async () => {
    try {
      await mavlinkAPI.land();
      alert('Land command sent.');
    } catch (e) {
      alert('Error while landing: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleRTL = async () => {
    try {
      await mavlinkAPI.returnToLaunch();
      alert('RTL (Return To Launch) command sent.');
    } catch (e) {
      alert('Error while RTL: ' + (e.response?.data?.detail || e.message));
    }
  };

  // =========================
  // Camera control (backend, not browser webcam)
  // =========================
  const startCamera = async () => {
    try {
      setCameraError('');
      // You can change the source (e.g., 1 or RTSP URL) if needed
      await imageAPI.startCamera(0);
      // Make sure detector mode is active (both YOLO and CV)
      await imageAPI.setMode('both');
      setIsCameraOn(true);
    } catch (err) {
      console.error(err);
      setCameraError(
        err.response?.data?.message || err.message || 'Error starting backend camera stream'
      );
      setIsCameraOn(false);
    }
  };

  const stopCamera = async () => {
    try {
      await imageAPI.stopCamera();
    } catch (err) {
      console.error('stopCamera error:', err);
    }
    setIsCameraOn(false);
  };

  if (showSplash) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-amber-50 via-stone-100 to-amber-100 flex items-center justify-center">
        <div className="text-center">
          <div className="flex items-center justify-center gap-4 mb-8">
            <span className="text-6xl text-green-700">✦</span>
            <h1 className="text-6xl font-light text-green-800 tracking-wider">
              Welcome to <span className="font-semibold">{typewriterText}</span>
              <span className="animate-pulse">|</span>
            </h1>
            <span className="text-6xl text-green-700">✦</span>
          </div>
          <div className="flex justify-center gap-2">
            <Sprout className="w-8 h-8 text-green-600 animate-bounce" style={{ animationDelay: '0ms' }} />
            <Leaf className="w-8 h-8 text-green-600 animate-bounce" style={{ animationDelay: '200ms' }} />
            <Sprout className="w-8 h-8 text-green-600 animate-bounce" style={{ animationDelay: '400ms' }} />
          </div>
        </div>
      </div>
    );
  }

  if (!showDashboard) return null;

  const rootBg = darkMode
    ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 text-slate-100'
    : 'bg-gradient-to-br from-stone-50 via-amber-50 to-green-50 text-slate-900';

  const cardBase = 'rounded-xl shadow-lg p-6 transition-all duration-300 border border-white/10';
  const cardBg = darkMode ? 'bg-slate-900/70 backdrop-blur' : 'bg-white';

  const navItemClasses = (tab) =>
    `flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-all ${
      activeTab === tab
        ? darkMode
          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        : darkMode
        ? 'text-slate-300 hover:bg-slate-800'
        : 'text-slate-600 hover:bg-slate-100'
    }`;

  // ===== Mission Config TAB =====
  const renderMissionConfig = () => (
    <div className="space-y-6">
      <div className={`${cardBase} ${cardBg}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-green-800 dark:text-emerald-200 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Mission Configuration
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-2 ${
              isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            <Radio className="w-3 h-3" />
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        <p className="text-xs text-gray-500 dark:text-gray-300 mb-4">
          Define your farm parameters and start the mission. This configuration will drive altitude,
          flight pattern and battery planning.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-green-700 dark:text-emerald-200 font-semibold mb-2">
              Farm Name *
            </label>
            <input
              type="text"
              required
              value={formData.farmName}
              onChange={(e) => setFormData({ ...formData, farmName: e.target.value })}
              className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:border-green-500 focus:outline-none"
              placeholder="e.g., Green Valley Orchards"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-green-700 dark:text-emerald-200 font-semibold mb-2">
                Farm Size (hectares) *
              </label>
              <input
                type="number"
                required
                step="0.1"
                value={formData.hectares}
                onChange={(e) => setFormData({ ...formData, hectares: e.target.value })}
                className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:border-green-500 focus:outline-none"
                placeholder="e.g., 5.5"
              />
            </div>
            <div>
              <label className="block text-green-700 dark:text-emerald-200 font-semibold mb-2">
                Tree Age (years) *
              </label>
              <input
                type="number"
                required
                value={formData.treeAge}
                onChange={(e) => setFormData({ ...formData, treeAge: e.target.value })}
                className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:border-green-500 focus:outline-none"
                placeholder="e.g., 8"
              />
            </div>
          </div>
          <div>
            <label className="block text-green-700 dark:text-emerald-200 font-semibold mb-2">
              Tree Species *
            </label>
            <select
              required
              value={formData.treeType}
              onChange={(e) => {
                setFormData({ ...formData, treeType: e.target.value });
              }}
              className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:border-green-500 focus:outline-none"
            >
              <option value="">Select a tree species</option>
              {Object.keys(TREE_GROWTH_DB)
                .sort()
                .map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
            </select>
          </div>

          {estimatedTreeHeight && recommendedAltitude && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 dark:bg-emerald-900/30 border border-green-200 dark:border-emerald-700 rounded-lg p-4">
                <p className="text-xs text-green-700 dark:text-emerald-200 mb-1">
                  Estimated Tree Height
                </p>
                <p className="text-2xl font-bold text-green-700 dark:text-emerald-100">
                  {estimatedTreeHeight.toFixed(2)} m
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                  Based on species <span className="font-semibold">{formData.treeType}</span> and age{' '}
                  <span className="font-semibold">{formData.treeAge} years</span>.
                </p>
              </div>
              <div className="bg-emerald-50 dark:bg-emerald-900/40 border border-emerald-300 dark:border-emerald-700 rounded-lg p-4">
                <p className="text-xs text-emerald-800 dark:text-emerald-100 mb-1">
                  Recommended Flight Altitude
                </p>
                <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-50">
                  {recommendedAltitude.toFixed(1)} m
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                  Canopy height + safety margin for imaging.
                </p>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-4 pt-4">
            <button
              type="button"
              onClick={handleDisconnect}
              className={`px-6 py-3 rounded-lg font-semibold text-sm border-2 ${
                isConnected
                  ? 'border-red-500 text-red-600 hover:bg-red-50'
                  : 'border-gray-300 text-gray-400 cursor-not-allowed'
              } transition-all`}
              disabled={!isConnected}
            >
              Disconnect
            </button>
            <button
              type="button"
              onClick={handleStartMission}
              className="flex-1 min-w-[160px] px-6 py-3 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-all transform hover:scale-105"
            >
              {flightData ? 'Update Mission Plan' : 'Start Mission'}
            </button>
          </div>
        </div>
      </div>

      {flightData && (
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
            <Plane className="w-5 h-5 text-green-500" />
            Current Mission Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-gray-500 dark:text-gray-300 text-xs mb-1">Farm</div>
              <div className="font-semibold">{formData.farmName || '—'}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {formData.hectares || '—'} ha · {formData.treeType || 'Unknown'} trees
              </div>
            </div>
            <div>
              <div className="text-gray-500 dark:text-gray-300 text-xs mb-1">Flight Profile</div>
              <div className="text-sm">
                {flightData.altitude} m · {flightData.duration} min
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {flightData.algorithm} pattern · {flightData.passes} passes
              </div>
            </div>
            <div>
              <div className="text-gray-500 dark:text-gray-300 text-xs mb-1">Status</div>
              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`px-2 py-1 rounded-full text-[11px] font-semibold ${
                    isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                <span className="text-gray-500 dark:text-gray-300 text-xs">
                  Battery {telemetry.battery.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // ===== Telemetry TAB =====
  const renderTelemetry = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {/* GPS Status */}
      <div className={`${cardBase} ${cardBg} border-l-4 border-l-green-500`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Satellite className="w-5 h-5 text-green-500" />
            GPS Status
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              telemetry.gps === 'RTK Fixed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {telemetry.gps}
          </span>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Satellites</span>
            <span className="font-bold text-green-700 dark:text-green-300">{telemetry.satellites}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Latitude</span>
            <span className="font-mono text-sm font-bold text-green-700 dark:text-green-300">
              {telemetry.lat.toFixed(6)}°
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Longitude</span>
            <span className="font-mono text-sm font-bold text-green-700 dark:text-green-300">
              {telemetry.lon.toFixed(6)}°
            </span>
          </div>
        </div>
      </div>

      {/* Battery */}
      <div className={`${cardBase} ${cardBg} border-l-4 border-l-amber-500`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Battery className="w-5 h-5 text-amber-500" />
            Battery
          </h3>
          <span className="text-2xl font-bold text-green-700 dark:text-green-300">
            {telemetry.battery.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              telemetry.battery > 50 ? 'bg-green-500' : telemetry.battery > 20 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${telemetry.battery}%` }}
          />
        </div>
      </div>

      {/* Flight Data */}
      <div className={`${cardBase} ${cardBg} border-l-4 border-l-blue-500`}>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
          <Navigation className="w-5 h-5 text-blue-500" />
          Flight Data
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Altitude</span>
            <span className="font-bold text-blue-600 dark:text-blue-300">
              {telemetry.altitude.toFixed(1)} m
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-500">Ground Speed</span>
            <span className="font-bold text-blue-600 dark:text-blue-300">
              {telemetry.speed.toFixed(1)} m/s
            </span>
          </div>
        </div>
      </div>

      {/* Mission Plan summary */}
      {flightData && (
        <div className={`${cardBase} bg-gradient-to-br from-green-600 to-green-700 text-white md:col-span-2 xl:col-span-3`}>
          <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
            <Plane className="w-5 h-5" />
            Mission Plan
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Farm</span>
              <div className="font-bold truncate">{formData.farmName || '—'}</div>
            </div>
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Optimal Altitude</span>
              <div className="font-bold">{flightData.altitude} m</div>
            </div>
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Est. Duration</span>
              <div className="font-bold">{flightData.duration} min</div>
            </div>
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Algorithm</span>
              <div className="font-bold">{flightData.algorithm}</div>
            </div>
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Coverage</span>
              <div className="font-bold">{(flightData.coverage / 10000).toFixed(1)} ha</div>
            </div>
            <div className="space-y-1">
              <span className="text-green-100 text-xs">Passes</span>
              <div className="font-bold">{flightData.passes}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // ===== Flight TAB =====
  const renderFlight = () => (
    <div className="space-y-6">
      <div className={`${cardBase} ${cardBg}`}>
        <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
          <MapPin className="w-5 h-5 text-green-500" />
          Field Map & Flight Path
        </h3>
        <div className="bg-gradient-to-br from-green-50 to-amber-50 dark:from-slate-800 dark:to-emerald-800 rounded-lg h-80 flex items-center justify-center border-2 border-dashed border-green-300 dark:border-emerald-500/60">
          <div className="text-center">
            <MapPin className="w-16 h-16 text-green-500 mx-auto mb-4 animate-bounce" />
            <p className="text-green-700 dark:text-emerald-200 font-semibold text-lg">
              Map Integration Ready
            </p>
            <p className="text-gray-500 dark:text-gray-300 text-sm mt-2">
              Connect to visualize flight path, boundaries and coverage in real-time.
            </p>
          </div>
        </div>
      </div>

      {/* Flight controls */}
      <div className={`${cardBase} ${cardBg}`}>
        <h3 className="text-lg font-bold text-green-800 dark:text-emerald-200 flex items-center gap-2 mb-4">
          <Plane className="w-5 h-5 text-green-500" />
          Flight Controls
        </h3>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleArm}
            disabled={!isConnected}
            className="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold disabled:bg-gray-300 disabled:text-gray-500"
          >
            Arm
          </button>
          <button
            onClick={handleTakeoff}
            disabled={!isConnected}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:bg-gray-300 disabled:text-gray-500"
          >
            Takeoff
          </button>
          <button
            onClick={handleLand}
            disabled={!isConnected}
            className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold disabled:bg-gray-300 disabled:text-gray-500"
          >
            Land
          </button>
          <button
            onClick={handleRTL}
            disabled={!isConnected}
            className="px-4 py-2 rounded-lg bg-amber-500 text-white text-sm font-semibold disabled:bg-gray-300 disabled:text-gray-500"
          >
            RTL
          </button>
        </div>
      </div>

      {flightData && (
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className="text-lg font-bold text-green-800 dark:text-emerald-200 flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Recommended Flight Strategy
          </h3>
          <div className="bg-gradient-to-r from-green-50 to-amber-50 dark:from-slate-800 dark:to-emerald-900 rounded-lg p-6">
            <div className="flex flex-col md:flex-row items-start gap-4">
              <CheckCircle2 className="w-8 h-8 text-green-600 flex-shrink-0 mt-1" />
              <div>
                <h4 className="text-xl font-bold text-green-800 dark:text-emerald-200 mb-2">
                  {flightData.algorithm} Pattern
                </h4>
                <p className="text-gray-700 dark:text-gray-200 mb-4 text-sm">
                  Based on your farm size of {formData.hectares || '—'} hectares and{' '}
                  {formData.terrainType} terrain, this algorithm provides optimal coverage with{' '}
                  {flightData.passes} flight passes.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-white/80 dark:bg-slate-900 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-emerald-300">
                      {flightData.altitude}m
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-300">Flight Height</div>
                  </div>
                  <div className="bg-white/80 dark:bg-slate-900 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-amber-600">{flightData.duration}min</div>
                    <div className="text-xs text-gray-600 dark:text-gray-300">Flight Time</div>
                  </div>
                  <div className="bg-white/80 dark:bg-slate-900 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.ceil(flightData.batteryNeeded / 100)}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-300">Batteries Needed</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!flightData && (
        <p className="text-sm text-gray-500 dark:text-gray-300">
          Configure a mission in the Mission Config tab to see flight strategy details.
        </p>
      )}
    </div>
  );

  // ===== Analysis TAB =====
  const renderAnalysis = () => {
    const total = yoloStats.total_processed || 0;
    const healthy = yoloStats.healthy_count || 0;
    const defective = yoloStats.defective_count || 0;
    const healthScore = healthOverview.score;

    return (
      <div className="space-y-6">
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className="text-lg font-bold text-green-800 dark:text-emerald-200 flex items-center gap-2 mb-4">
            <Leaf className="w-5 h-5 text-green-500" />
            Tree Health Analysis (YOLO + CV)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-green-50 dark:bg-emerald-900/40 rounded-lg p-4 text-center border-2 border-green-200 dark:border-emerald-600/70">
              <div className="text-3xl font-bold text-green-600 dark:text-emerald-300">{healthy}</div>
              <div className="text-sm text-green-700 dark:text-emerald-200 mt-1">Healthy</div>
            </div>
            <div className="bg-amber-50 dark:bg-amber-900/40 rounded-lg p-4 text-center border-2 border-amber-200 dark:border-amber-500/80">
              <div className="text-3xl font-bold text-amber-600">{defective}</div>
              <div className="text-sm text-amber-700 dark:text-amber-200 mt-1">
                Defective / Stressed
              </div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 text-center border-2 border-slate-200 dark:border-slate-600">
              <div className="text-3xl font-bold text-slate-700 dark:text-slate-100">{total}</div>
              <div className="text-sm text-slate-700 dark:text-slate-200 mt-1">Total Detections</div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-emerald-50 dark:bg-emerald-900/30 rounded-lg p-4 border border-emerald-200 dark:border-emerald-700">
              <div className="text-xs text-emerald-700 dark:text-emerald-200 mb-1">
                Overall Health Score
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-emerald-700 dark:text-emerald-200">
                  {healthScore != null ? healthScore.toFixed(1) : '—'}
                </span>
                <span className="text-sm text-emerald-800 dark:text-emerald-100">/ 100</span>
              </div>
              <div className="text-sm mt-2 text-emerald-800 dark:text-emerald-100">
                Status: <span className="font-semibold">{healthOverview.status}</span>
              </div>
            </div>

            <div className="flex flex-col justify-center items-start text-sm text-gray-600 dark:text-gray-200">
              <p>
                This panel summarizes the health of the field based on YOLO detections and classical
                CV metrics such as NDVI-like indices, texture and green coverage.
              </p>
              <p className="mt-2">
                For live data, turn the camera on in the <strong>Camera</strong> tab so the backend
                can process the drone video stream in real time.
              </p>
            </div>
          </div>
        </div>

        <div className={`${cardBase} ${cardBg}`}>
          <h3 className="text-lg font-bold flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-emerald-500" />
            Yield & Health Insights
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            In the future this area can host NDVI heatmaps, time-series of health scores, and yield
            estimation charts for each mission.
          </p>
        </div>
      </div>
    );
  };

  // ===== Camera TAB =====
  const renderCamera = () => (
    <div className="space-y-6">
      <div className={`${cardBase} ${cardBg}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Camera className="w-5 h-5 text-green-500" />
            Live Drone Camera (Backend)
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              isCameraOn ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
            }`}
          >
            {isCameraOn ? 'Streaming' : 'Idle'}
          </span>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          This view connects to the backend video stream on port 8001
          (<code className="mx-1">/api/camera/stream</code>) while YOLO and classical CV run on
          every frame.
        </p>

        <div className="flex flex-wrap gap-4 mb-4">
          <button
            type="button"
            onClick={startCamera}
            className="px-5 py-2 rounded-lg text-sm font-semibold bg-green-600 text-white hover:bg-green-700 transition-all disabled:opacity-50"
            disabled={isCameraOn}
          >
            Start Drone Camera
          </button>
          <button
            type="button"
            onClick={stopCamera}
            className="px-5 py-2 rounded-lg text-sm font-semibold border border-red-500 text-red-600 hover:bg-red-50 transition-all disabled:opacity-50"
            disabled={!isCameraOn}
          >
            Stop Camera
          </button>
        </div>

        {cameraError && (
          <div className="mb-4 text-sm text-red-500 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{cameraError}</span>
          </div>
        )}

        <div className="rounded-xl overflow-hidden border border-green-300 dark:border-emerald-600 bg-black/80 flex items-center justify-center h-80">
          {isCameraOn ? (
            <img
              src={imageAPI.getStreamURL()}
              alt="Drone camera stream"
              className="w-full h-full object-contain bg-black"
            />
          ) : (
            <div className="text-gray-500 text-sm">
              Camera is off. Click <strong>Start Drone Camera</strong> to begin streaming.
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen p-6 animate-fade-in ${rootBg}`}>
      {/* Header */}
      <header className="bg-gradient-to-r from-green-700 to-green-600 rounded-2xl shadow-2xl p-6 mb-6 animate-slide-down">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-amber-100/90 p-3 rounded-xl">
              <Sprout className="w-8 h-8 text-green-700" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">AgriVision Pro</h1>
              <p className="text-green-100 text-sm">Precision Agriculture Drone System</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode((prev) => !prev)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/20 hover:bg-black/30 text-amber-100 text-sm font-medium transition-all"
            >
              {darkMode ? (
                <>
                  <Sun className="w-4 h-4" />
                  Light
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4" />
                  Dark
                </>
              )}
            </button>

            {/* Link status */}
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              } text-white`}
            >
              <Radio className="w-5 h-5" />
              <span className="font-semibold">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Layout: Sidebar + Content */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <aside className={`${cardBase} ${cardBg} lg:w-60 flex-shrink-0 h-fit`}>
          <h3 className="text-sm font-semibold mb-3 text-gray-500 dark:text-gray-300">Dashboard</h3>
          <div className="space-y-2">
            <button className={navItemClasses('mission')} onClick={() => setActiveTab('mission')}>
              <Settings className="w-4 h-4" />
              Mission Config
            </button>
            <button className={navItemClasses('telemetry')} onClick={() => setActiveTab('telemetry')}>
              <Satellite className="w-4 h-4" />
              Telemetry
            </button>
            <button className={navItemClasses('flight')} onClick={() => setActiveTab('flight')}>
              <Plane className="w-4 h-4" />
              Flight & Map
            </button>
            <button className={navItemClasses('analysis')} onClick={() => setActiveTab('analysis')}>
              <Leaf className="w-4 h-4" />
              Analysis (YOLO)
            </button>
            <button className={navItemClasses('camera')} onClick={() => setActiveTab('camera')}>
              <Camera className="w-4 h-4" />
              Camera
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 space-y-6">
          {activeTab === 'mission' && renderMissionConfig()}
          {activeTab === 'telemetry' && renderTelemetry()}
          {activeTab === 'flight' && renderFlight()}
          {activeTab === 'analysis' && renderAnalysis()}
          {activeTab === 'camera' && renderCamera()}
        </main>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes slide-down {
          from {
            transform: translateY(-20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        @keyframes slide-right {
          from {
            transform: translateX(-20px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes slide-left {
          from {
            transform: translateX(20px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes scale-in {
          from {
            transform: scale(0.9);
            opacity: 0;
          }
          to {
            transform: scale(1);
            opacity: 1;
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out;
        }
        .animate-slide-down {
          animation: slide-down 0.6s ease-out;
        }
        .animate-slide-right {
          animation: slide-right 0.6s ease-out;
        }
        .animate-slide-left {
          animation: slide-left 0.6s ease-out;
        }
        .animate-scale-in {
          animation: scale-in 0.4s ease-out;
        }
      `}</style>
    </div>
  );
};

export default AgriculturalDroneDashboard;
