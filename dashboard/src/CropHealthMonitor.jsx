import React, { useState } from 'react';
import { Upload, Image as ImageIcon, Leaf, TrendingUp, AlertTriangle, CheckCircle, XCircle, Loader } from 'lucide-react';

const CropHealthMonitor = ({ darkMode = false, t = (key) => key }) => {
  // Dark mode classes
  const bgClass = darkMode ? 'bg-gray-900' : 'bg-gradient-to-br from-green-50 to-blue-50';
  const cardBgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-gray-100' : 'text-gray-800';
  const borderClass = darkMode ? 'border-gray-700' : 'border-gray-300';
  const inputBgClass = darkMode ? 'bg-gray-700 text-white' : 'bg-white';

  const [selectedCrop, setSelectedCrop] = useState('apple');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('single');

  const API_BASE_URL = 'http://localhost:8000';

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
      setAnalysisResult(null);
      setError(null);
    }
  };

  const analyzeImage = async () => {
    if (!uploadedImage) {
      setError(t('pleaseUploadImage'));
      return;
    }

    setAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', uploadedImage);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/health/analyze?crop_type=${selectedCrop}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`${t('analysisFailed')}: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const getHealthColor = (health) => {
    if (darkMode) {
      if (health >= 90) return 'text-green-400';
      if (health >= 75) return 'text-lime-400';
      if (health >= 50) return 'text-yellow-400';
      if (health >= 25) return 'text-orange-400';
      return 'text-red-400';
    } else {
      if (health >= 90) return 'text-green-600';
      if (health >= 75) return 'text-lime-600';
      if (health >= 50) return 'text-yellow-600';
      if (health >= 25) return 'text-orange-600';
      return 'text-red-600';
    }
  };

  const getHealthIcon = (status) => {
    if (status === 'Excellent' || status === 'Good') return <CheckCircle className={`w-6 h-6 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />;
    if (status === 'Fair') return <AlertTriangle className={`w-6 h-6 ${darkMode ? 'text-yellow-400' : 'text-yellow-600'}`} />;
    return <XCircle className={`w-6 h-6 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />;
  };

  return (
    <div className={`min-h-screen ${bgClass} p-6`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className={`text-4xl font-bold ${textClass} mb-2 flex items-center gap-3`}>
            <Leaf className="w-10 h-10 text-green-600" />
            {t('cropHealthMonitor')}
          </h1>
          <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>{t('aiPoweredDiseaseDetection')}</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Upload & Controls */}
          <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
            <h2 className={`text-2xl font-bold ${textClass} mb-4 flex items-center gap-2`}>
              <Upload className="w-6 h-6 text-blue-600" />
              {t('imageUpload')}
            </h2>

            {/* Crop Selection */}
            <div className="mb-6">
              <label className={`block text-sm font-medium ${textClass} mb-2`}>
                {t('selectCropType')}
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

            {/* Image Upload Area */}
            <div className="mb-6">
              <label
                htmlFor="image-upload"
                className={`block w-full border-2 border-dashed ${borderClass} rounded-lg p-8 text-center cursor-pointer transition-all ${darkMode ? 'hover:border-blue-400 hover:bg-gray-700' : 'hover:border-blue-500 hover:bg-blue-50'}`}
              >
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt={t('preview')}
                    className="max-h-64 mx-auto rounded-lg"
                  />
                ) : (
                  <div className={darkMode ? 'text-gray-400' : 'text-gray-500'}>
                    <ImageIcon className={`w-16 h-16 mx-auto mb-4 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
                    <p className={`text-lg font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>{t('clickToUploadImage')}</p>
                    <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'} mt-2`}>{t('pngJpgUpTo10MB')}</p>
                  </div>
                )}
                <input
                  id="image-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Analyze Button */}
            <button
              onClick={analyzeImage}
              disabled={!uploadedImage || analyzing}
              className={`w-full py-4 px-6 rounded-lg font-bold text-white text-lg transition-all ${
                !uploadedImage || analyzing
                  ? darkMode ? 'bg-gray-600 cursor-not-allowed' : 'bg-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600 shadow-lg'
              }`}
            >
              {analyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  {t('analyzing')}...
                </span>
              ) : (
                t('analyzeCropHealth')
              )}
            </button>

            {/* Error Display */}
            {error && (
              <div className={`mt-4 p-4 ${darkMode ? 'bg-red-900 bg-opacity-30 border-red-700 text-red-300' : 'bg-red-50 border-red-200 text-red-700'} border rounded-lg`}>
                <p className="font-medium">{t('error')}:</p>
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Right Panel - Results */}
          <div className={`${cardBgClass} rounded-xl shadow-lg p-6`}>
            <h2 className={`text-2xl font-bold ${textClass} mb-4 flex items-center gap-2`}>
              <TrendingUp className="w-6 h-6 text-green-600" />
              {t('analysisResults')}
            </h2>

            {analysisResult ? (
              <div className="space-y-6">
                {/* Overall Health */}
                <div className={`${darkMode ? 'bg-gradient-to-br from-blue-900 to-green-900 bg-opacity-30' : 'bg-gradient-to-br from-blue-50 to-green-50'} rounded-lg p-6`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className={`text-lg font-semibold ${textClass}`}>{t('overallHealth')}</h3>
                    {getHealthIcon(analysisResult.report.status)}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-5xl font-bold ${getHealthColor(analysisResult.report.overall_health)}`}>
                      {analysisResult.report.overall_health.toFixed(1)}%
                    </span>
                    <span className={`text-xl ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      {analysisResult.report.status}
                    </span>
                  </div>
                </div>

                {/* Disease Summary */}
                <div>
                  <h3 className={`text-lg font-semibold ${textClass} mb-3`}>{t('diseaseDetection')}</h3>
                  <div className="space-y-2">
                    {Object.entries(analysisResult.report.disease_summary).map(([disease, count]) => (
                      <div key={disease} className={`flex justify-between items-center p-3 ${darkMode ? 'bg-gray-700 bg-opacity-40' : 'bg-gray-50'} rounded-lg`}>
                        <span className={`font-medium capitalize ${textClass}`}>{disease.replace(/_/g, ' ')}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                          disease === 'healthy'
                            ? darkMode ? 'bg-green-900 bg-opacity-40 text-green-300' : 'bg-green-100 text-green-700'
                            : darkMode ? 'bg-red-900 bg-opacity-40 text-red-300' : 'bg-red-100 text-red-700'
                        }`}>
                          {count} {t('detected')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Damage Statistics */}
                {analysisResult.report.damaged_area_stats && (
                  <div>
                    <h3 className={`text-lg font-semibold ${textClass} mb-3`}>{t('damageAnalysis')}</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className={`${darkMode ? 'bg-orange-900 bg-opacity-30' : 'bg-orange-50'} rounded-lg p-4`}>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('damagedAreas')}</p>
                        <p className={`text-2xl font-bold ${darkMode ? 'text-orange-400' : 'text-orange-600'}`}>
                          {analysisResult.report.damaged_area_stats.total_damaged_areas}
                        </p>
                      </div>
                      <div className={`${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded-lg p-4`}>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>{t('damagePercentage')}</p>
                        <p className={`text-2xl font-bold ${darkMode ? 'text-red-400' : 'text-red-600'}`}>
                          {analysisResult.report.damaged_area_stats.damage_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {analysisResult.report.recommendations && analysisResult.report.recommendations.length > 0 && (
                  <div>
                    <h3 className={`text-lg font-semibold ${textClass} mb-3`}>{t('recommendations')}</h3>
                    <div className="space-y-2">
                      {analysisResult.report.recommendations.map((rec, idx) => (
                        <div key={idx} className={`flex gap-2 p-3 ${darkMode ? 'bg-blue-900 bg-opacity-30' : 'bg-blue-50'} rounded-lg`}>
                          <AlertTriangle className={`w-5 h-5 ${darkMode ? 'text-blue-400' : 'text-blue-600'} flex-shrink-0 mt-0.5`} />
                          <p className={`text-sm ${textClass}`}>{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Visualizations */}
                <div>
                  <h3 className={`text-lg font-semibold ${textClass} mb-3`}>{t('healthVisualizations')}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {analysisResult.visualizations.health_map && (
                      <div>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-2`}>{t('healthMap')}</p>
                        <img
                          src={`data:image/jpeg;base64,${analysisResult.visualizations.health_map}`}
                          alt={t('healthMap')}
                          className={`w-full rounded-lg border-2 ${borderClass}`}
                        />
                      </div>
                    )}
                    {analysisResult.visualizations.contour_map && (
                      <div>
                        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-2`}>{t('contourMap')}</p>
                        <img
                          src={`data:image/jpeg;base64,${analysisResult.visualizations.contour_map}`}
                          alt={t('contourMap')}
                          className={`w-full rounded-lg border-2 ${borderClass}`}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className={`flex flex-col items-center justify-center h-64 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                <Leaf className="w-16 h-16 mb-4" />
                <p className="text-lg">{t('uploadAndAnalyzeImage')}</p>
              </div>
            )}
          </div>
        </div>

        {/* Disease Info Cards */}
        <div className={`mt-8 ${cardBgClass} rounded-xl shadow-lg p-6`}>
          <h2 className={`text-2xl font-bold ${textClass} mb-4`}>{t('detectableDiseases')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Apple Diseases */}
            <div>
              <h3 className={`text-xl font-semibold mb-3 ${darkMode ? 'text-red-400' : 'text-red-600'}`}>🍎 {t('appleDiseases')}</h3>
              <ul className="space-y-2">
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-green-900 bg-opacity-30' : 'bg-green-50'} rounded`}>
                  <CheckCircle className={`w-4 h-4 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
                  <span className={textClass}>{t('healthy')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('appleScab')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('blackRot')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('cedarAppleRust')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('powderyMildew')}</span>
                </li>
              </ul>
            </div>

            {/* Soybean Diseases */}
            <div>
              <h3 className={`text-xl font-semibold mb-3 ${darkMode ? 'text-green-400' : 'text-green-600'}`}>🌱 {t('soybeanDiseases')}</h3>
              <ul className="space-y-2">
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-green-900 bg-opacity-30' : 'bg-green-50'} rounded`}>
                  <CheckCircle className={`w-4 h-4 ${darkMode ? 'text-green-400' : 'text-green-600'}`} />
                  <span className={textClass}>{t('healthy')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('bacterialBlight')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('caterpillar')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('diabroticaSpeciosa')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('downyMildew')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('mosaicVirus')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('powderyMildew')}</span>
                </li>
                <li className={`flex items-center gap-2 p-2 ${darkMode ? 'bg-red-900 bg-opacity-30' : 'bg-red-50'} rounded`}>
                  <AlertTriangle className={`w-4 h-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`} />
                  <span className={textClass}>{t('rust')}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CropHealthMonitor;
