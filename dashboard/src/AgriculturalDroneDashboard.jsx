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
  Apple,
  Upload,
} from 'lucide-react';

import { mavlinkAPI } from './api/mavlink';
import { imageAPI, appleCounterAPI } from './api/imageProcessor';
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

const AgriculturalDroneDashboard = ({ darkMode = false, t = (key) => key }) => {
  // Dark mode class variables
  const bgClass = darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-blue-50 to-green-50';
  const cardBgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-gray-100' : 'text-gray-800';
  const borderClass = darkMode ? 'border-gray-700' : 'border-gray-300';
  const inputBgClass = darkMode ? 'bg-gray-700 text-white' : 'bg-white';

  const [showSplash, setShowSplash] = useState(true);
  const [typewriterText, setTypewriterText] = useState('');
  const [showDashboard, setShowDashboard] = useState(false);
  const [darkModeInternal, setDarkModeInternal] = useState(darkMode);
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

  // Apple Counter state
  const [appleCounterFile, setAppleCounterFile] = useState(null);
  const [appleCounterPreview, setAppleCounterPreview] = useState(null);
  const [appleCounterLoading, setAppleCounterLoading] = useState(false);
  const [appleCounterResults, setAppleCounterResults] = useState(null);
  const [appleCounterError, setAppleCounterError] = useState('');

  // Use internal or prop darkMode
  const activeDarkMode = darkMode || darkModeInternal;

  // =========================
  // Splash typewriter
  // =========================
  useEffect(() => {
    const text = t('modern_farming');
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
  }, [t]);

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
      alert(t('error_mission_api'));
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
      alert(t('drone_armed'));
    } catch (e) {
      alert(t('error_arming') + ': ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleTakeoff = async () => {
    try {
      const alt = flightData?.altitude || recommendedAltitude || 10;
      await mavlinkAPI.takeoff(alt);
      alert(t('takeoff_command_sent') + ` ${alt} m.`);
    } catch (e) {
      alert(t('error_takeoff') + ': ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleLand = async () => {
    try {
      await mavlinkAPI.land();
      alert(t('land_command_sent'));
    } catch (e) {
      alert(t('error_landing') + ': ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleRTL = async () => {
    try {
      await mavlinkAPI.returnToLaunch();
      alert(t('rtl_command_sent'));
    } catch (e) {
      alert(t('error_rtl') + ': ' + (e.response?.data?.detail || e.message));
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
        err.response?.data?.message || err.message || t('error_camera_stream')
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

  // =========================
  // Apple Counter handlers
  // =========================
  const handleAppleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAppleCounterFile(file);
      setAppleCounterPreview(URL.createObjectURL(file));
      setAppleCounterResults(null);
      setAppleCounterError('');
    }
  };

  const handleCountApples = async () => {
    if (!appleCounterFile) {
      setAppleCounterError(t('pleaseUploadImage'));
      return;
    }

    setAppleCounterLoading(true);
    setAppleCounterError('');

    try {
      const results = await appleCounterAPI.countApples(appleCounterFile);
      setAppleCounterResults(results);
    } catch (err) {
      console.error('Apple counting error:', err);
      setAppleCounterError(err.response?.data?.detail || err.message || t('analysisFailed'));
    } finally {
      setAppleCounterLoading(false);
    }
  };

  const resetAppleCounter = () => {
    setAppleCounterFile(null);
    setAppleCounterPreview(null);
    setAppleCounterResults(null);
    setAppleCounterError('');
  };

  if (showSplash) {
    return (
      <div className={`fixed inset-0 ${activeDarkMode ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-emerald-950' : 'bg-gradient-to-br from-amber-50 via-stone-100 to-amber-100'} flex items-center justify-center`}>
        <div className="text-center">
          <div className="flex items-center justify-center gap-4 mb-8">
            <span className={`text-6xl ${activeDarkMode ? 'text-green-400' : 'text-green-700'}`}>✦</span>
            <h1 className={`text-6xl font-light ${activeDarkMode ? 'text-green-300' : 'text-green-800'} tracking-wider`}>
              {t('welcome_to')} <span className="font-semibold">{typewriterText}</span>
              <span className="animate-pulse">|</span>
            </h1>
            <span className={`text-6xl ${activeDarkMode ? 'text-green-400' : 'text-green-700'}`}>✦</span>
          </div>
          <div className="flex justify-center gap-2">
            <Sprout className={`w-8 h-8 ${activeDarkMode ? 'text-green-400' : 'text-green-600'} animate-bounce`} style={{ animationDelay: '0ms' }} />
            <Leaf className={`w-8 h-8 ${activeDarkMode ? 'text-green-400' : 'text-green-600'} animate-bounce`} style={{ animationDelay: '200ms' }} />
            <Sprout className={`w-8 h-8 ${activeDarkMode ? 'text-green-400' : 'text-green-600'} animate-bounce`} style={{ animationDelay: '400ms' }} />
          </div>
        </div>
      </div>
    );
  }

  if (!showDashboard) return null;

  const rootBg = activeDarkMode
    ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 text-slate-100'
    : 'bg-gradient-to-br from-stone-50 via-amber-50 to-green-50 text-slate-900';

  const cardBase = 'rounded-xl shadow-lg p-6 transition-all duration-300 border';
  const cardBg = activeDarkMode ? 'bg-slate-900/70 backdrop-blur border-gray-700' : 'bg-white border-white/10';

  const navItemClasses = (tab) =>
    `flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-all ${
      activeTab === tab
        ? activeDarkMode
          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
        : activeDarkMode
        ? 'text-slate-300 hover:bg-slate-800'
        : 'text-slate-600 hover:bg-slate-100'
    }`;

  // ===== Mission Config TAB =====
  const renderMissionConfig = () => (
    <div className="space-y-6">
      <div className={`${cardBase} ${cardBg}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'} flex items-center gap-2`}>
            <Settings className="w-5 h-5" />
            {t('mission_configuration')}
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-2 ${
              isConnected
                ? activeDarkMode
                  ? 'bg-green-900 bg-opacity-50 text-green-300'
                  : 'bg-green-100 text-green-700'
                : activeDarkMode
                  ? 'bg-red-900 bg-opacity-50 text-red-300'
                  : 'bg-red-100 text-red-700'
            }`}
          >
            <Radio className="w-3 h-3" />
            {isConnected ? t('connected') : t('disconnected')}
          </span>
        </div>

        <p className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} mb-4`}>
          {t('mission_config_description')}
        </p>

        <div className="space-y-4">
          <div>
            <label className={`block ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} font-semibold mb-2`}>
              {t('farm_name')} *
            </label>
            <input
              type="text"
              required
              value={formData.farmName}
              onChange={(e) => setFormData({ ...formData, farmName: e.target.value })}
              className={`w-full px-4 py-3 border-2 ${activeDarkMode ? 'border-gray-600 bg-gray-700 text-white focus:border-emerald-500' : 'border-green-200 bg-white focus:border-green-500'} rounded-lg focus:outline-none`}
              placeholder={t('farm_name_placeholder')}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={`block ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} font-semibold mb-2`}>
                {t('farm_size_hectares')} *
              </label>
              <input
                type="number"
                required
                step="0.1"
                value={formData.hectares}
                onChange={(e) => setFormData({ ...formData, hectares: e.target.value })}
                className={`w-full px-4 py-3 border-2 ${activeDarkMode ? 'border-gray-600 bg-gray-700 text-white focus:border-emerald-500' : 'border-green-200 bg-white focus:border-green-500'} rounded-lg focus:outline-none`}
                placeholder={t('hectares_placeholder')}
              />
            </div>
            <div>
              <label className={`block ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} font-semibold mb-2`}>
                {t('tree_age_years')} *
              </label>
              <input
                type="number"
                required
                value={formData.treeAge}
                onChange={(e) => setFormData({ ...formData, treeAge: e.target.value })}
                className={`w-full px-4 py-3 border-2 ${activeDarkMode ? 'border-gray-600 bg-gray-700 text-white focus:border-emerald-500' : 'border-green-200 bg-white focus:border-green-500'} rounded-lg focus:outline-none`}
                placeholder={t('tree_age_placeholder')}
              />
            </div>
          </div>
          <div>
            <label className={`block ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} font-semibold mb-2`}>
              {t('tree_species')} *
            </label>
            <select
              required
              value={formData.treeType}
              onChange={(e) => {
                setFormData({ ...formData, treeType: e.target.value });
              }}
              className={`w-full px-4 py-3 border-2 ${activeDarkMode ? 'border-gray-600 bg-gray-700 text-white focus:border-emerald-500' : 'border-green-200 bg-white focus:border-green-500'} rounded-lg focus:outline-none`}
            >
              <option value="">{t('select_tree_species')}</option>
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
              <div className={`${activeDarkMode ? 'bg-emerald-900 bg-opacity-30 border-emerald-700' : 'bg-green-50 border-green-200'} border rounded-lg p-4`}>
                <p className={`text-xs ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} mb-1`}>
                  {t('estimated_tree_height')}
                </p>
                <p className={`text-2xl font-bold ${activeDarkMode ? 'text-emerald-100' : 'text-green-700'}`}>
                  {estimatedTreeHeight.toFixed(2)} m
                </p>
                <p className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'} mt-1`}>
                  {t('based_on_species')} <span className="font-semibold">{formData.treeType}</span> {t('and_age')}{' '}
                  <span className="font-semibold">{formData.treeAge} {t('years')}</span>.
                </p>
              </div>
              <div className={`${activeDarkMode ? 'bg-emerald-900 bg-opacity-40 border-emerald-700' : 'bg-emerald-50 border-emerald-300'} border rounded-lg p-4`}>
                <p className={`text-xs ${activeDarkMode ? 'text-emerald-100' : 'text-emerald-800'} mb-1`}>
                  {t('recommended_flight_altitude')}
                </p>
                <p className={`text-2xl font-bold ${activeDarkMode ? 'text-emerald-50' : 'text-emerald-700'}`}>
                  {recommendedAltitude.toFixed(1)} m
                </p>
                <p className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'} mt-1`}>
                  {t('canopy_height_safety_margin')}
                </p>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-4 pt-4">
            <button
              type="button"
              onClick={handleDisconnect}
              className={`px-6 py-3 rounded-lg font-semibold text-sm border-2 transition-all ${
                isConnected
                  ? activeDarkMode
                    ? 'border-red-500 text-red-400 hover:bg-red-900 hover:bg-opacity-30'
                    : 'border-red-500 text-red-600 hover:bg-red-50'
                  : activeDarkMode
                    ? 'border-gray-600 text-gray-500 cursor-not-allowed'
                    : 'border-gray-300 text-gray-400 cursor-not-allowed'
              }`}
              disabled={!isConnected}
            >
              {t('disconnect')}
            </button>
            <button
              type="button"
              onClick={handleStartMission}
              className={`flex-1 min-w-[160px] px-6 py-3 ${activeDarkMode ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-green-600 hover:bg-green-700'} text-white rounded-lg font-semibold text-sm transition-all transform hover:scale-105`}
            >
              {flightData ? t('update_mission_plan') : t('start_mission')}
            </button>
          </div>
        </div>
      </div>

      {flightData && (
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'}`}>
            <Plane className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
            {t('current_mission_summary')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className={`${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} text-xs mb-1`}>{t('farm')}</div>
              <div className={`font-semibold ${textClass}`}>{formData.farmName || '—'}</div>
              <div className={`text-xs ${activeDarkMode ? 'text-gray-400' : 'text-gray-500'} mt-1`}>
                {formData.hectares || '—'} {t('ha')} · {formData.treeType || t('unknown')} {t('trees')}
              </div>
            </div>
            <div>
              <div className={`${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} text-xs mb-1`}>{t('flight_profile')}</div>
              <div className={`text-sm ${textClass}`}>
                {flightData.altitude} m · {flightData.duration} {t('min')}
              </div>
              <div className={`text-xs ${activeDarkMode ? 'text-gray-400' : 'text-gray-500'} mt-1`}>
                {flightData.algorithm} {t('pattern')} · {flightData.passes} {t('passes')}
              </div>
            </div>
            <div>
              <div className={`${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} text-xs mb-1`}>{t('status')}</div>
              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`px-2 py-1 rounded-full text-[11px] font-semibold ${
                    isConnected
                      ? activeDarkMode
                        ? 'bg-green-900 bg-opacity-50 text-green-300'
                        : 'bg-green-100 text-green-700'
                      : activeDarkMode
                        ? 'bg-red-900 bg-opacity-50 text-red-300'
                        : 'bg-red-100 text-red-700'
                  }`}
                >
                  {isConnected ? t('connected') : t('disconnected')}
                </span>
                <span className={`${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} text-xs`}>
                  {t('battery')} {telemetry.battery.toFixed(0)}%
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
      <div className={`${cardBase} ${cardBg} border-l-4 ${activeDarkMode ? 'border-l-emerald-500' : 'border-l-green-500'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-bold flex items-center gap-2 ${textClass}`}>
            <Satellite className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
            {t('gps_status')}
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              telemetry.gps === 'RTK Fixed'
                ? activeDarkMode
                  ? 'bg-green-900 bg-opacity-50 text-green-300'
                  : 'bg-green-100 text-green-700'
                : activeDarkMode
                  ? 'bg-red-900 bg-opacity-50 text-red-300'
                  : 'bg-red-100 text-red-700'
            }`}
          >
            {telemetry.gps}
          </span>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className={activeDarkMode ? 'text-gray-400' : 'text-gray-500'}>{t('satellites')}</span>
            <span className={`font-bold ${activeDarkMode ? 'text-green-300' : 'text-green-700'}`}>{telemetry.satellites}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className={activeDarkMode ? 'text-gray-400' : 'text-gray-500'}>{t('latitude')}</span>
            <span className={`font-mono text-sm font-bold ${activeDarkMode ? 'text-green-300' : 'text-green-700'}`}>
              {telemetry.lat.toFixed(6)}°
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className={activeDarkMode ? 'text-gray-400' : 'text-gray-500'}>{t('longitude')}</span>
            <span className={`font-mono text-sm font-bold ${activeDarkMode ? 'text-green-300' : 'text-green-700'}`}>
              {telemetry.lon.toFixed(6)}°
            </span>
          </div>
        </div>
      </div>

      {/* Battery */}
      <div className={`${cardBase} ${cardBg} border-l-4 ${activeDarkMode ? 'border-l-amber-400' : 'border-l-amber-500'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-bold flex items-center gap-2 ${textClass}`}>
            <Battery className={`w-5 h-5 ${activeDarkMode ? 'text-amber-400' : 'text-amber-500'}`} />
            {t('battery')}
          </h3>
          <span className={`text-2xl font-bold ${activeDarkMode ? 'text-green-300' : 'text-green-700'}`}>
            {telemetry.battery.toFixed(1)}%
          </span>
        </div>
        <div className={`w-full ${activeDarkMode ? 'bg-gray-700' : 'bg-gray-200'} rounded-full h-3 overflow-hidden`}>
          <div
            className={`h-full transition-all duration-500 ${
              telemetry.battery > 50 ? 'bg-green-500' : telemetry.battery > 20 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${telemetry.battery}%` }}
          />
        </div>
      </div>

      {/* Flight Data */}
      <div className={`${cardBase} ${cardBg} border-l-4 ${activeDarkMode ? 'border-l-blue-400' : 'border-l-blue-500'}`}>
        <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${textClass}`}>
          <Navigation className={`w-5 h-5 ${activeDarkMode ? 'text-blue-400' : 'text-blue-500'}`} />
          {t('flight_data')}
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className={activeDarkMode ? 'text-gray-400' : 'text-gray-500'}>{t('altitude')}</span>
            <span className={`font-bold ${activeDarkMode ? 'text-blue-300' : 'text-blue-600'}`}>
              {telemetry.altitude.toFixed(1)} m
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className={activeDarkMode ? 'text-gray-400' : 'text-gray-500'}>{t('ground_speed')}</span>
            <span className={`font-bold ${activeDarkMode ? 'text-blue-300' : 'text-blue-600'}`}>
              {telemetry.speed.toFixed(1)} m/s
            </span>
          </div>
        </div>
      </div>

      {/* Mission Plan summary */}
      {flightData && (
        <div className={`${cardBase} ${activeDarkMode ? 'bg-gradient-to-br from-emerald-800 to-emerald-900 border-emerald-700' : 'bg-gradient-to-br from-green-600 to-green-700 border-green-500'} text-white md:col-span-2 xl:col-span-3`}>
          <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
            <Plane className="w-5 h-5" />
            {t('mission_plan')}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('farm')}</span>
              <div className="font-bold truncate">{formData.farmName || '—'}</div>
            </div>
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('optimal_altitude')}</span>
              <div className="font-bold">{flightData.altitude} m</div>
            </div>
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('est_duration')}</span>
              <div className="font-bold">{flightData.duration} {t('min')}</div>
            </div>
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('algorithm')}</span>
              <div className="font-bold">{flightData.algorithm}</div>
            </div>
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('coverage')}</span>
              <div className="font-bold">{(flightData.coverage / 10000).toFixed(1)} {t('ha')}</div>
            </div>
            <div className="space-y-1">
              <span className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-100'} text-xs`}>{t('passes')}</span>
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
        <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'}`}>
          <MapPin className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
          {t('field_map_flight_path')}
        </h3>
        <div className={`${activeDarkMode ? 'bg-gradient-to-br from-slate-800 to-emerald-900 border-emerald-500' : 'bg-gradient-to-br from-green-50 to-amber-50 border-green-300'} rounded-lg h-80 flex items-center justify-center border-2 border-dashed`}>
          <div className="text-center">
            <MapPin className={`w-16 h-16 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'} mx-auto mb-4 animate-bounce`} />
            <p className={`${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} font-semibold text-lg`}>
              {t('map_integration_ready')}
            </p>
            <p className={`${activeDarkMode ? 'text-gray-300' : 'text-gray-500'} text-sm mt-2`}>
              {t('connect_to_visualize')}
            </p>
          </div>
        </div>
      </div>

      {/* Flight controls */}
      <div className={`${cardBase} ${cardBg}`}>
        <h3 className={`text-lg font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'} flex items-center gap-2 mb-4`}>
          <Plane className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
          {t('flight_controls')}
        </h3>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleArm}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeDarkMode ? 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 disabled:text-gray-500' : 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-300 disabled:text-gray-500'} text-white transition-all`}
          >
            {t('arm')}
          </button>
          <button
            onClick={handleTakeoff}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeDarkMode ? 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500' : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500'} text-white transition-all`}
          >
            {t('takeoff')}
          </button>
          <button
            onClick={handleLand}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeDarkMode ? 'bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:text-gray-500' : 'bg-red-600 hover:bg-red-700 disabled:bg-gray-300 disabled:text-gray-500'} text-white transition-all`}
          >
            {t('land')}
          </button>
          <button
            onClick={handleRTL}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg text-sm font-semibold ${activeDarkMode ? 'bg-amber-500 hover:bg-amber-600 disabled:bg-gray-700 disabled:text-gray-500' : 'bg-amber-500 hover:bg-amber-600 disabled:bg-gray-300 disabled:text-gray-500'} text-white transition-all`}
          >
            {t('rtl')}
          </button>
        </div>
      </div>

      {flightData && (
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className={`text-lg font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'} flex items-center gap-2 mb-4`}>
            <TrendingUp className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
            {t('recommended_flight_strategy')}
          </h3>
          <div className={`${activeDarkMode ? 'bg-gradient-to-r from-slate-800 to-emerald-900' : 'bg-gradient-to-r from-green-50 to-amber-50'} rounded-lg p-6`}>
            <div className="flex flex-col md:flex-row items-start gap-4">
              <CheckCircle2 className={`w-8 h-8 ${activeDarkMode ? 'text-emerald-400' : 'text-green-600'} flex-shrink-0 mt-1`} />
              <div>
                <h4 className={`text-xl font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'} mb-2`}>
                  {flightData.algorithm} {t('pattern')}
                </h4>
                <p className={`${activeDarkMode ? 'text-gray-200' : 'text-gray-700'} mb-4 text-sm`}>
                  {t('based_on_farm_size')} {formData.hectares || '—'} {t('hectares')} {t('and')}{' '}
                  {formData.terrainType} {t('terrain')}, {t('algorithm_provides')} {flightData.passes} {t('flight_passes')}.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className={`${activeDarkMode ? 'bg-slate-900 border border-gray-700' : 'bg-white/80'} rounded-lg p-3 text-center`}>
                    <div className={`text-2xl font-bold ${activeDarkMode ? 'text-emerald-300' : 'text-green-600'}`}>
                      {flightData.altitude}m
                    </div>
                    <div className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t('flight_height')}</div>
                  </div>
                  <div className={`${activeDarkMode ? 'bg-slate-900 border border-gray-700' : 'bg-white/80'} rounded-lg p-3 text-center`}>
                    <div className={`text-2xl font-bold ${activeDarkMode ? 'text-amber-400' : 'text-amber-600'}`}>{flightData.duration}{t('min')}</div>
                    <div className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t('flight_time')}</div>
                  </div>
                  <div className={`${activeDarkMode ? 'bg-slate-900 border border-gray-700' : 'bg-white/80'} rounded-lg p-3 text-center`}>
                    <div className={`text-2xl font-bold ${activeDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                      {Math.ceil(flightData.batteryNeeded / 100)}
                    </div>
                    <div className={`text-xs ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t('batteries_needed')}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!flightData && (
        <p className={`text-sm ${activeDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>
          {t('configure_mission_to_see_strategy')}
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
          <h3 className={`text-lg font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-green-800'} flex items-center gap-2 mb-4`}>
            <Leaf className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
            {t('tree_health_analysis')}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className={`${activeDarkMode ? 'bg-emerald-900 bg-opacity-40 border-emerald-600' : 'bg-green-50 border-green-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-emerald-300' : 'text-green-600'}`}>{healthy}</div>
              <div className={`text-sm ${activeDarkMode ? 'text-emerald-200' : 'text-green-700'} mt-1`}>{t('healthy')}</div>
            </div>
            <div className={`${activeDarkMode ? 'bg-amber-900 bg-opacity-40 border-amber-500' : 'bg-amber-50 border-amber-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-amber-400' : 'text-amber-600'}`}>{defective}</div>
              <div className={`text-sm ${activeDarkMode ? 'text-amber-200' : 'text-amber-700'} mt-1`}>
                {t('defective_stressed')}
              </div>
            </div>
            <div className={`${activeDarkMode ? 'bg-slate-800 border-slate-600' : 'bg-slate-50 border-slate-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-slate-100' : 'text-slate-700'}`}>{total}</div>
              <div className={`text-sm ${activeDarkMode ? 'text-slate-200' : 'text-slate-700'} mt-1`}>{t('total_detections')}</div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`${activeDarkMode ? 'bg-emerald-900 bg-opacity-30 border-emerald-700' : 'bg-emerald-50 border-emerald-200'} rounded-lg p-4 border`}>
              <div className={`text-xs ${activeDarkMode ? 'text-emerald-200' : 'text-emerald-700'} mb-1`}>
                {t('overall_health_score')}
              </div>
              <div className="flex items-baseline gap-2">
                <span className={`text-3xl font-bold ${activeDarkMode ? 'text-emerald-200' : 'text-emerald-700'}`}>
                  {healthScore != null ? healthScore.toFixed(1) : '—'}
                </span>
                <span className={`text-sm ${activeDarkMode ? 'text-emerald-100' : 'text-emerald-800'}`}>/ 100</span>
              </div>
              <div className={`text-sm mt-2 ${activeDarkMode ? 'text-emerald-100' : 'text-emerald-800'}`}>
                {t('status')}: <span className="font-semibold">{healthOverview.status}</span>
              </div>
            </div>

            <div className={`flex flex-col justify-center items-start text-sm ${activeDarkMode ? 'text-gray-200' : 'text-gray-600'}`}>
              <p>
                {t('health_panel_description')}
              </p>
              <p className="mt-2">
                {t('for_live_data_turn_camera_on')} <strong>{t('camera')}</strong> {t('tab_for_live_processing')}.
              </p>
            </div>
          </div>
        </div>

        <div className={`${cardBase} ${cardBg}`}>
          <h3 className={`text-lg font-bold flex items-center gap-2 mb-2 ${textClass}`}>
            <TrendingUp className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-emerald-500'}`} />
            {t('yield_health_insights')}
          </h3>
          <p className={`text-sm ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            {t('future_area_description')}
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
          <h3 className={`text-lg font-bold flex items-center gap-2 ${textClass}`}>
            <Camera className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-green-500'}`} />
            {t('live_drone_camera')}
          </h3>
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              isCameraOn
                ? activeDarkMode
                  ? 'bg-green-900 bg-opacity-50 text-green-300'
                  : 'bg-green-100 text-green-700'
                : activeDarkMode
                  ? 'bg-gray-700 text-gray-300'
                  : 'bg-gray-200 text-gray-600'
            }`}
          >
            {isCameraOn ? t('streaming') : t('idle')}
          </span>
        </div>

        <p className={`text-sm ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-4`}>
          {t('camera_description')}
          (<code className="mx-1">/api/camera/stream</code>) {t('while_yolo_cv_run')}.
        </p>

        <div className="flex flex-wrap gap-4 mb-4">
          <button
            type="button"
            onClick={startCamera}
            className={`px-5 py-2 rounded-lg text-sm font-semibold ${activeDarkMode ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-green-600 hover:bg-green-700'} text-white transition-all disabled:opacity-50`}
            disabled={isCameraOn}
          >
            {t('start_drone_camera')}
          </button>
          <button
            type="button"
            onClick={stopCamera}
            className={`px-5 py-2 rounded-lg text-sm font-semibold border ${activeDarkMode ? 'border-red-500 text-red-400 hover:bg-red-900 hover:bg-opacity-30' : 'border-red-500 text-red-600 hover:bg-red-50'} transition-all disabled:opacity-50`}
            disabled={!isCameraOn}
          >
            {t('stop_camera')}
          </button>
        </div>

        {cameraError && (
          <div className="mb-4 text-sm text-red-500 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{cameraError}</span>
          </div>
        )}

        <div className={`rounded-xl overflow-hidden border ${activeDarkMode ? 'border-emerald-600 bg-black' : 'border-green-300 bg-black/80'} flex items-center justify-center h-80`}>
          {isCameraOn ? (
            <img
              src={imageAPI.getStreamURL()}
              alt={t('drone_camera_stream')}
              className="w-full h-full object-contain bg-black"
            />
          ) : (
            <div className={`${activeDarkMode ? 'text-gray-400' : 'text-gray-500'} text-sm`}>
              {t('camera_off_message')} <strong>{t('start_drone_camera')}</strong> {t('to_begin_streaming')}.
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ===== Apple Counter TAB =====
  const renderAppleCounter = () => (
    <div className="space-y-6">
      <div className={`${cardBase} ${cardBg}`}>
        <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${activeDarkMode ? 'text-red-300' : 'text-red-700'}`}>
          <Apple className={`w-5 h-5 ${activeDarkMode ? 'text-red-400' : 'text-red-500'}`} />
          {t('apple_counter')}
        </h3>
        <p className={`text-sm ${activeDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-4`}>
          {t('apple_counter_description')}
        </p>

        {/* Upload Section */}
        <div className="mb-6">
          <label
            htmlFor="apple-file-input"
            className={`flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
              activeDarkMode
                ? 'border-red-600 bg-red-900/20 hover:bg-red-900/30'
                : 'border-red-300 bg-red-50 hover:bg-red-100'
            }`}
          >
            {appleCounterPreview ? (
              <img
                src={appleCounterPreview}
                alt="Preview"
                className="max-h-36 object-contain rounded-lg"
              />
            ) : (
              <div className="flex flex-col items-center">
                <Upload className={`w-10 h-10 mb-2 ${activeDarkMode ? 'text-red-400' : 'text-red-500'}`} />
                <span className={`text-sm ${activeDarkMode ? 'text-red-300' : 'text-red-600'}`}>
                  {t('clickToUploadImage')}
                </span>
                <span className={`text-xs mt-1 ${activeDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {t('pngJpgUpTo10MB')}
                </span>
              </div>
            )}
            <input
              id="apple-file-input"
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAppleFileChange}
            />
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-4">
          <button
            type="button"
            onClick={handleCountApples}
            disabled={!appleCounterFile || appleCounterLoading}
            className={`px-6 py-3 rounded-lg text-sm font-semibold ${
              activeDarkMode ? 'bg-red-600 hover:bg-red-700' : 'bg-red-600 hover:bg-red-700'
            } text-white transition-all disabled:opacity-50`}
          >
            {appleCounterLoading ? t('analyzing') : t('count_apples')}
          </button>
          {appleCounterResults && (
            <button
              type="button"
              onClick={resetAppleCounter}
              className={`px-6 py-3 rounded-lg text-sm font-semibold border ${
                activeDarkMode
                  ? 'border-gray-500 text-gray-300 hover:bg-gray-800'
                  : 'border-gray-400 text-gray-600 hover:bg-gray-100'
              } transition-all`}
            >
              {t('newMission')}
            </button>
          )}
        </div>

        {/* Error Message */}
        {appleCounterError && (
          <div className="mb-4 text-sm text-red-500 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{appleCounterError}</span>
          </div>
        )}
      </div>

      {/* Results Section */}
      {appleCounterResults && (
        <div className={`${cardBase} ${cardBg}`}>
          <h3 className={`text-lg font-bold flex items-center gap-2 mb-4 ${textClass}`}>
            <CheckCircle2 className={`w-5 h-5 ${activeDarkMode ? 'text-emerald-400' : 'text-emerald-500'}`} />
            {t('counting_results')}
          </h3>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className={`${activeDarkMode ? 'bg-red-900/40 border-red-600' : 'bg-red-50 border-red-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-red-300' : 'text-red-600'}`}>
                {appleCounterResults.total_apples}
              </div>
              <div className={`text-sm ${activeDarkMode ? 'text-red-200' : 'text-red-700'} mt-1`}>
                {t('total_apples')}
              </div>
            </div>
            <div className={`${activeDarkMode ? 'bg-emerald-900/40 border-emerald-600' : 'bg-emerald-50 border-emerald-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-emerald-300' : 'text-emerald-600'}`}>
                {appleCounterResults.healthy_apples}
              </div>
              <div className={`text-sm ${activeDarkMode ? 'text-emerald-200' : 'text-emerald-700'} mt-1`}>
                {t('healthy_apples')}
              </div>
            </div>
            <div className={`${activeDarkMode ? 'bg-amber-900/40 border-amber-500' : 'bg-amber-50 border-amber-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-amber-400' : 'text-amber-600'}`}>
                {appleCounterResults.unhealthy_apples}
              </div>
              <div className={`text-sm ${activeDarkMode ? 'text-amber-200' : 'text-amber-700'} mt-1`}>
                {t('unhealthy_apples')}
              </div>
            </div>
            <div className={`${activeDarkMode ? 'bg-blue-900/40 border-blue-500' : 'bg-blue-50 border-blue-200'} rounded-lg p-4 text-center border-2`}>
              <div className={`text-3xl font-bold ${activeDarkMode ? 'text-blue-300' : 'text-blue-600'}`}>
                {appleCounterResults.health_percentage.toFixed(1)}%
              </div>
              <div className={`text-sm ${activeDarkMode ? 'text-blue-200' : 'text-blue-700'} mt-1`}>
                {t('health_percentage')}
              </div>
            </div>
          </div>

          {/* Status Badge */}
          <div className="mb-6">
            <span className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${
              appleCounterResults.health_percentage >= 75
                ? activeDarkMode ? 'bg-emerald-900/50 text-emerald-300' : 'bg-emerald-100 text-emerald-700'
                : appleCounterResults.health_percentage >= 50
                ? activeDarkMode ? 'bg-amber-900/50 text-amber-300' : 'bg-amber-100 text-amber-700'
                : activeDarkMode ? 'bg-red-900/50 text-red-300' : 'bg-red-100 text-red-700'
            }`}>
              {t('status')}: {appleCounterResults.status_text}
            </span>
          </div>

          {/* Visualization */}
          {appleCounterResults.visualization && (
            <div className={`rounded-xl overflow-hidden border ${activeDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
              <img
                src={`data:image/jpeg;base64,${appleCounterResults.visualization}`}
                alt="Apple detection visualization"
                className="w-full object-contain"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className={`min-h-screen p-6 animate-fade-in ${rootBg}`}>
      {/* Header */}
      <header className={`${activeDarkMode ? 'bg-gradient-to-r from-emerald-800 to-emerald-700' : 'bg-gradient-to-r from-green-700 to-green-600'} rounded-2xl shadow-2xl p-6 mb-6 animate-slide-down`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`${activeDarkMode ? 'bg-emerald-900/50' : 'bg-amber-100/90'} p-3 rounded-xl`}>
              <Sprout className={`w-8 h-8 ${activeDarkMode ? 'text-emerald-300' : 'text-green-700'}`} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">{t('agrivision_pro')}</h1>
              <p className={`${activeDarkMode ? 'text-emerald-100' : 'text-green-100'} text-sm`}>{t('precision_agriculture_drone_system')}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkModeInternal((prev) => !prev)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg ${activeDarkMode ? 'bg-black/30 hover:bg-black/40' : 'bg-black/20 hover:bg-black/30'} ${activeDarkMode ? 'text-amber-200' : 'text-amber-100'} text-sm font-medium transition-all`}
            >
              {activeDarkMode ? (
                <>
                  <Sun className="w-4 h-4" />
                  {t('light')}
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4" />
                  {t('dark')}
                </>
              )}
            </button>

            {/* Link status */}
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                isConnected
                  ? activeDarkMode
                    ? 'bg-emerald-600'
                    : 'bg-green-500'
                  : 'bg-red-500'
              } text-white`}
            >
              <Radio className="w-5 h-5" />
              <span className="font-semibold">{isConnected ? t('connected') : t('disconnected')}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Layout: Sidebar + Content */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <aside className={`${cardBase} ${cardBg} lg:w-60 flex-shrink-0 h-fit`}>
          <h3 className={`text-sm font-semibold mb-3 ${activeDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>{t('dashboard')}</h3>
          <div className="space-y-2">
            <button className={navItemClasses('mission')} onClick={() => setActiveTab('mission')}>
              <Settings className="w-4 h-4" />
              {t('mission_config')}
            </button>
            <button className={navItemClasses('telemetry')} onClick={() => setActiveTab('telemetry')}>
              <Satellite className="w-4 h-4" />
              {t('telemetry')}
            </button>
            <button className={navItemClasses('flight')} onClick={() => setActiveTab('flight')}>
              <Plane className="w-4 h-4" />
              {t('flight_and_map')}
            </button>
            <button className={navItemClasses('analysis')} onClick={() => setActiveTab('analysis')}>
              <Leaf className="w-4 h-4" />
              {t('analysis_yolo')}
            </button>
            <button className={navItemClasses('camera')} onClick={() => setActiveTab('camera')}>
              <Camera className="w-4 h-4" />
              {t('camera')}
            </button>
            <button className={navItemClasses('appleCounter')} onClick={() => setActiveTab('appleCounter')}>
              <Apple className="w-4 h-4" />
              {t('apple_counter')}
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
          {activeTab === 'appleCounter' && renderAppleCounter()}
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
