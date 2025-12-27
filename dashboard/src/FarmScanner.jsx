import React, { useState } from 'react';
import { Upload, Image as ImageIcon, MapPin, TrendingUp, AlertTriangle, CheckCircle, Download, Loader, TreeDeciduous, Leaf } from 'lucide-react';

const FarmScanner = ({ darkMode = false, t = (key) => key }) => {
  // Dark mode classes
  const bgClass = darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-green-50 to-blue-50';
  const cardBgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-gray-100' : 'text-gray-800';
  const borderClass = darkMode ? 'border-gray-700' : 'border-gray-300';
  const hoverClass = darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100';
  const inputBgClass = darkMode ? 'bg-gray-700 text-white' : 'bg-white';
  const stepBgActive = darkMode ? 'bg-green-600' : 'bg-green-500';
  const stepBgInactive = darkMode ? 'bg-gray-700' : 'bg-gray-200';

  const [selectedCrop, setSelectedCrop] = useState('apple');
  const [uploadedImages, setUploadedImages] = useState([]);
  const [missionParams, setMissionParams] = useState({
    hectares: '1',
    treeSpacing: '5',
    flightAltitude: '15',
    overlap: '0.3'
  });
  const [missionPlan, setMissionPlan] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [missionReport, setMissionReport] = useState(null);
  const [error, setError] = useState(null);
  const [activeStep, setActiveStep] = useState(1); // 1: Plan, 2: Upload, 3: Results

  const API_BASE_URL = 'http://localhost:8000';

  const handleParamChange = (e) => {
    setMissionParams({
      ...missionParams,
      [e.target.name]: e.target.value
    });
  };

  const planMission = async () => {
    setError(null);
    setProcessing(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/mission/plan?` +
        `hectares=${missionParams.hectares}&` +
        `crop_type=${selectedCrop}&` +
        `tree_spacing=${missionParams.treeSpacing}&` +
        `flight_altitude=${missionParams.flightAltitude}&` +
        `overlap=${missionParams.overlap}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`Mission planning failed: ${response.statusText}`);
      }

      const data = await response.json();
      setMissionPlan(data.mission_plan);
      setActiveStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleImagesUpload = (event) => {
    const files = Array.from(event.target.files);
    setUploadedImages(files);
    setError(null);
  };

  const processFarmImages = async () => {
    if (uploadedImages.length === 0) {
      setError('Please upload at least one farm image');
      return;
    }

    setProcessing(true);
    setError(null);

    const formData = new FormData();
    uploadedImages.forEach(file => {
      formData.append('files', file);
    });

    try {
      // Batch process all images
      const response = await fetch(
        `${API_BASE_URL}/api/mission/batch-process`,
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error(`Processing failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Get the full mission report
      const reportResponse = await fetch(`${API_BASE_URL}/api/mission/report`);
      if (!reportResponse.ok) {
        throw new Error(`Report generation failed`);
      }

      const reportData = await reportResponse.json();
      setMissionReport(reportData.report);
      setActiveStep(3);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const downloadReport = async (format) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mission/export?format=${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `farm_mission_report.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(`Download failed: ${err.message}`);
    }
  };

  const resetMission = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/mission/reset`, { method: 'DELETE' });
      setMissionPlan(null);
      setMissionReport(null);
      setUploadedImages([]);
      setActiveStep(1);
      setError(null);
    } catch (err) {
      setError(`Reset failed: ${err.message}`);
    }
  };

  return (
    <div className={`min-h-screen ${bgClass} p-6`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className={`text-4xl font-bold ${textClass} mb-2 flex items-center gap-3`}>
            <TreeDeciduous className="w-10 h-10 text-green-600" />
            {t('farmScannerTitle')}
          </h1>
          <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>{t('farmScannerSubtitle')}</p>
        </div>

        {/* Step Indicators */}
        <div className={`mb-8 ${cardBgClass} rounded-xl shadow-lg p-6`}>
          <div className="flex items-center justify-between">
            <div className={`flex items-center gap-3 ${activeStep >= 1 ? 'text-green-600' : darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${activeStep >= 1 ? stepBgActive + ' text-white' : stepBgInactive}`}>
                1
              </div>
              <span className="font-medium">{t('planMission')}</span>
            </div>

            <div className={`flex-1 h-1 mx-4 ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
              <div className={`h-full transition-all ${activeStep >= 2 ? 'bg-green-500 w-full' : 'w-0'}`}></div>
            </div>

            <div className={`flex items-center gap-3 ${activeStep >= 2 ? 'text-green-600' : darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${activeStep >= 2 ? stepBgActive + ' text-white' : stepBgInactive}`}>
                2
              </div>
              <span className="font-medium">{t('uploadImages')}</span>
            </div>

            <div className={`flex-1 h-1 mx-4 ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
              <div className={`h-full transition-all ${activeStep >= 3 ? 'bg-green-500 w-full' : 'w-0'}`}></div>
            </div>

            <div className={`flex items-center gap-3 ${activeStep >= 3 ? 'text-green-600' : darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${activeStep >= 3 ? stepBgActive + ' text-white' : stepBgInactive}`}>
                3
              </div>
              <span className="font-medium">{t('viewResults')}</span>
            </div>
          </div>
        </div>

        {/* Step 1: Mission Planning */}
        {activeStep === 1 && (
          <div className={`${cardBgClass} rounded-xl shadow-lg p-6 mb-6`}>
            <h2 className={`text-2xl font-bold ${textClass} mb-6 flex items-center gap-2`}>
              <MapPin className="w-6 h-6 text-blue-600" />
              {t('missionParameters')}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Crop Selection */}
              <div>
                <label className={`block text-sm font-medium ${textClass} mb-2`}>
                  {t('cropType')}
                </label>
                <div className="flex gap-4">
                  <button
                    onClick={() => setSelectedCrop('apple')}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                      selectedCrop === 'apple'
                        ? 'bg-red-500 text-white shadow-lg'
                        : darkMode ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    🍎 {t('apple')}
                  </button>
                  <button
                    onClick={() => setSelectedCrop('soybean')}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                      selectedCrop === 'soybean'
                        ? 'bg-green-500 text-white shadow-lg'
                        : darkMode ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    🌱 {t('soybean')}
                  </button>
                </div>
              </div>

              {/* Farm Area */}
              <div>
                <label className={`block text-sm font-medium ${textClass} mb-2`}>
                  {t('farmArea')} (hectares)
                </label>
                <input
                  type="number"
                  name="hectares"
                  value={missionParams.hectares}
                  onChange={handleParamChange}
                  className={`w-full px-4 py-3 border ${borderClass} rounded-lg focus:ring-2 focus:ring-blue-500 ${inputBgClass}`}
                  min="0.1"
                  step="0.1"
                />
              </div>

              {/* Tree Spacing */}
              <div>
                <label className={`block text-sm font-medium ${textClass} mb-2`}>
                  {t('treeSpacing')} (meters)
                </label>
                <input
                  type="number"
                  name="treeSpacing"
                  value={missionParams.treeSpacing}
                  onChange={handleParamChange}
                  className={`w-full px-4 py-3 border ${borderClass} rounded-lg focus:ring-2 focus:ring-blue-500 ${inputBgClass}`}
                  min="1"
                  step="0.5"
                />
              </div>

              {/* Flight Altitude */}
              <div>
                <label className={`block text-sm font-medium ${textClass} mb-2`}>
                  {t('flightAltitude')} (meters)
                </label>
                <input
                  type="number"
                  name="flightAltitude"
                  value={missionParams.flightAltitude}
                  onChange={handleParamChange}
                  className={`w-full px-4 py-3 border ${borderClass} rounded-lg focus:ring-2 focus:ring-blue-500 ${inputBgClass}`}
                  min="5"
                  max="50"
                />
              </div>

              {/* Image Overlap */}
              <div className="md:col-span-2">
                <label className={`block text-sm font-medium ${textClass} mb-2`}>
                  {t('imageOverlap')}: {(parseFloat(missionParams.overlap) * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  name="overlap"
                  value={missionParams.overlap}
                  onChange={handleParamChange}
                  className="w-full"
                  min="0.1"
                  max="0.6"
                  step="0.1"
                />
              </div>
            </div>

            <button
              onClick={planMission}
              disabled={processing}
              className="mt-6 w-full py-4 px-6 bg-gradient-to-r from-blue-500 to-green-500 text-white rounded-lg font-bold text-lg hover:from-blue-600 hover:to-green-600 transition-all shadow-lg disabled:opacity-50"
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  {t('planning')}...
                </span>
              ) : (
                t('planFarmMission')
              )}
            </button>
          </div>
        )}

        {/* Step 2: Image Upload */}
        {activeStep === 2 && missionPlan && (
          <div className="space-y-6">
            {/* Mission Plan Summary */}
            <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
              <h2 className={`text-2xl font-bold ${textClass} mb-4`}>{t('missionReady')}</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className={`${darkMode ? 'bg-blue-900 bg-opacity-30' : 'bg-blue-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('farmArea')}</p>
                  <p className={`text-2xl font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>{missionPlan.farm_area_hectares} ha</p>
                </div>
                <div className={`${darkMode ? 'bg-green-900 bg-opacity-30' : 'bg-green-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('estimatedTrees')}</p>
                  <p className={`text-2xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>{missionPlan.estimated_trees}</p>
                </div>
                <div className={`${darkMode ? 'bg-purple-900 bg-opacity-30' : 'bg-purple-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('waypoints')}</p>
                  <p className={`text-2xl font-bold ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>{missionPlan.total_waypoints}</p>
                </div>
                <div className={`${darkMode ? 'bg-orange-900 bg-opacity-30' : 'bg-orange-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('altitude')}</p>
                  <p className={`text-2xl font-bold ${darkMode ? 'text-orange-400' : 'text-orange-600'}`}>{missionPlan.flight_altitude}m</p>
                </div>
              </div>
            </div>

            {/* Image Upload */}
            <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
              <h2 className={`text-2xl font-bold ${textClass} mb-4 flex items-center gap-2`}>
                <Upload className="w-6 h-6 text-blue-600" />
                {t('uploadFarmImages')}
              </h2>

              <label
                htmlFor="farm-images"
                className={`block w-full border-2 border-dashed ${borderClass} rounded-lg p-8 text-center cursor-pointer transition-all ${darkMode ? 'hover:border-blue-400 hover:bg-gray-700' : 'hover:border-blue-500 hover:bg-blue-50'}`}
              >
                <ImageIcon className={`w-16 h-16 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
                <p className={`text-lg font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{t('clickUploadMultiple')}</p>
                <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'} mt-2`}>PNG, JPG - {t('uploadDroneImages')}</p>
                {uploadedImages.length > 0 && (
                  <p className="text-green-600 font-medium mt-4">{uploadedImages.length} {t('imagesSelected')}</p>
                )}
                <input
                  id="farm-images"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImagesUpload}
                  className="hidden"
                />
              </label>

              <button
                onClick={processFarmImages}
                disabled={!uploadedImages.length || processing}
                className="mt-6 w-full py-4 px-6 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg font-bold text-lg hover:from-green-600 hover:to-blue-600 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {processing ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader className="w-5 h-5 animate-spin" />
                    {t('processing')} {uploadedImages.length} {t('images')}...
                  </span>
                ) : (
                  `${t('processImages')} ${uploadedImages.length || 0} ${t('images')}`
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {activeStep === 3 && missionReport && (
          <div className="space-y-6">
            {/* Farm Summary */}
            <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
              <div className="flex items-center justify-between mb-6">
                <h2 className={`text-2xl font-bold ${textClass} flex items-center gap-2`}>
                  <TrendingUp className="w-6 h-6 text-green-600" />
                  {t('farmHealthReport')}
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => downloadReport('json')}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    JSON
                  </button>
                  <button
                    onClick={() => downloadReport('csv')}
                    className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    CSV
                  </button>
                  <button
                    onClick={resetMission}
                    className={`px-4 py-2 ${darkMode ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-500 text-white hover:bg-gray-600'} rounded-lg`}
                  >
                    {t('newMission')}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className={`${darkMode ? 'bg-blue-900 bg-opacity-30' : 'bg-blue-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('totalTrees')}</p>
                  <p className={`text-3xl font-bold ${darkMode ? 'text-blue-400' : 'text-blue-600'}`}>{missionReport.farm_summary.total_trees}</p>
                </div>
                <div className={`${darkMode ? 'bg-green-900 bg-opacity-30' : 'bg-green-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('healthyTrees')}</p>
                  <p className={`text-3xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>{missionReport.farm_summary.healthy_trees}</p>
                </div>
                <div className={`${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('diseasedTrees')}</p>
                  <p className={`text-3xl font-bold ${darkMode ? 'text-red-400' : 'text-red-600'}`}>{missionReport.farm_summary.diseased_trees}</p>
                </div>
                <div className={`${darkMode ? 'bg-purple-900 bg-opacity-30' : 'bg-purple-50'} rounded-lg p-4`}>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('avgHealth')}</p>
                  <p className={`text-3xl font-bold ${darkMode ? 'text-purple-400' : 'text-purple-600'}`}>{missionReport.farm_summary.average_health_score}%</p>
                </div>
              </div>

              <div className={`${darkMode ? 'bg-gray-700 bg-opacity-50' : 'bg-gradient-to-r from-blue-50 to-green-50'} rounded-lg p-6`}>
                <h3 className={`text-lg font-semibold ${textClass} mb-2`}>{t('overallFarmHealth')}</h3>
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-bold ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                    {missionReport.farm_summary.health_percentage}%
                  </span>
                  <span className={`text-xl ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>{t('ofTreesHealthy')}</span>
                </div>
              </div>
            </div>

            {/* Disease Distribution */}
            {Object.keys(missionReport.disease_distribution).length > 0 && (
              <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
                <h3 className={`text-xl font-semibold ${textClass} mb-4`}>{t('diseaseDistribution')}</h3>
                <div className="space-y-2">
                  {Object.entries(missionReport.disease_distribution).map(([disease, count]) => (
                    <div key={disease} className={`flex justify-between items-center p-3 ${darkMode ? 'bg-gray-700 bg-opacity-40' : 'bg-gray-50'} rounded-lg`}>
                      <span className={`font-medium capitalize ${textClass}`}>{disease.replace(/_/g, ' ')}</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                        disease.toLowerCase().includes('healthy')
                          ? darkMode ? 'bg-green-900 bg-opacity-40 text-green-300' : 'bg-green-100 text-green-700'
                          : darkMode ? 'bg-red-900 bg-opacity-40 text-red-300' : 'bg-red-100 text-red-700'
                      }`}>
                        {count} {t('trees')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Health Visualizations */}
            <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
              <h3 className={`text-xl font-semibold ${textClass} mb-4`}>{t('farmHealthMap')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-2`}>{t('healthDistributionMap')}</p>
                  <img
                    src={`data:image/jpeg;base64,${missionReport.visualizations.health_map}`}
                    alt="Health Map"
                    className={`w-full rounded-lg border-2 ${borderClass}`}
                  />
                </div>
                <div>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-2`}>{t('contourMapLocations')}</p>
                  <img
                    src={`data:image/jpeg;base64,${missionReport.visualizations.contour_map}`}
                    alt="Contour Map"
                    className={`w-full rounded-lg border-2 ${borderClass}`}
                  />
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {missionReport.recommendations && missionReport.recommendations.length > 0 && (
              <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
                <h3 className={`text-xl font-semibold ${textClass} mb-4`}>{t('treatmentRecommendations')}</h3>
                <div className="space-y-2">
                  {missionReport.recommendations.map((rec, idx) => (
                    <div key={idx} className={`flex gap-3 p-4 ${darkMode ? 'bg-amber-900 bg-opacity-30 border-amber-700' : 'bg-amber-50 border-amber-500'} rounded-lg border-l-4`}>
                      <AlertTriangle className={`w-5 h-5 ${darkMode ? 'text-amber-400' : 'text-amber-600'} flex-shrink-0 mt-0.5`} />
                      <p className={textClass}>{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tree Log (truncated) */}
            <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
              <h3 className={`text-xl font-semibold ${textClass} mb-4`}>{t('individualTreeLog')} ({t('first10')})</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className={darkMode ? 'bg-gray-700 bg-opacity-50' : 'bg-gray-50'}>
                    <tr>
                      <th className={`px-4 py-2 text-left text-sm font-medium ${textClass}`}>{t('treeId')}</th>
                      <th className={`px-4 py-2 text-left text-sm font-medium ${textClass}`}>{t('location')} (X, Y)</th>
                      <th className={`px-4 py-2 text-left text-sm font-medium ${textClass}`}>{t('health')}</th>
                      <th className={`px-4 py-2 text-left text-sm font-medium ${textClass}`}>{t('status')}</th>
                      <th className={`px-4 py-2 text-left text-sm font-medium ${textClass}`}>{t('diseases')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {missionReport.tree_log.slice(0, 10).map((tree, idx) => (
                      <tr key={idx} className={`${darkMode ? 'border-gray-700' : 'border-gray-200'} border-t`}>
                        <td className={`px-4 py-3 font-mono text-sm ${textClass}`}>{tree.tree_id}</td>
                        <td className={`px-4 py-3 text-sm ${textClass}`}>
                          ({tree.gps_location.x.toFixed(1)}, {tree.gps_location.y.toFixed(1)})
                        </td>
                        <td className="px-4 py-3">
                          <span className={`font-bold ${
                            tree.health_score >= 80 ? darkMode ? 'text-green-400' : 'text-green-600' :
                            tree.health_score >= 60 ? darkMode ? 'text-yellow-400' : 'text-yellow-600' :
                            darkMode ? 'text-red-400' : 'text-red-600'
                          }`}>
                            {tree.health_score.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {tree.status === 'Healthy' ? (
                            <CheckCircle className={`w-5 h-5 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
                          ) : (
                            <AlertTriangle className={`w-5 h-5 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                          )}
                        </td>
                        <td className={`px-4 py-3 text-sm ${textClass}`}>
                          {tree.diseases.length > 0 ? tree.diseases.join(', ') : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {missionReport.tree_log.length > 10 && (
                  <p className={`text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mt-4`}>
                    {t('showing10Of')} {missionReport.tree_log.length} {t('trees')}. {t('downloadFullReport')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className={`${darkMode ? 'bg-red-900 bg-opacity-30 border-red-700 text-red-300' : 'bg-red-50 border-red-200 text-red-700'} border rounded-lg p-4`}>
            <p className="font-medium">{t('error')}:</p>
            <p>{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FarmScanner;
