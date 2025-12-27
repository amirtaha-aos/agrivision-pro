import React, { useState } from 'react';
import { Upload, Image as ImageIcon, Leaf, TrendingUp, AlertTriangle, CheckCircle, XCircle, Loader } from 'lucide-react';

const CropHealthMonitor = () => {
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
      setError('Please upload an image first');
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
        throw new Error(`Analysis failed: ${response.statusText}`);
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
    if (health >= 90) return 'text-green-600';
    if (health >= 75) return 'text-lime-600';
    if (health >= 50) return 'text-yellow-600';
    if (health >= 25) return 'text-orange-600';
    return 'text-red-600';
  };

  const getHealthIcon = (status) => {
    if (status === 'Excellent' || status === 'Good') return <CheckCircle className="w-6 h-6 text-green-600" />;
    if (status === 'Fair') return <AlertTriangle className="w-6 h-6 text-yellow-600" />;
    return <XCircle className="w-6 h-6 text-red-600" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <Leaf className="w-10 h-10 text-green-600" />
            Crop Health Monitor
          </h1>
          <p className="text-gray-600">AI-powered disease detection for apple and soybean crops</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Upload & Controls */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Upload className="w-6 h-6 text-blue-600" />
              Image Upload
            </h2>

            {/* Crop Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Crop Type
              </label>
              <div className="flex gap-4">
                <button
                  onClick={() => setSelectedCrop('apple')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                    selectedCrop === 'apple'
                      ? 'bg-red-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🍎 Apple
                </button>
                <button
                  onClick={() => setSelectedCrop('soybean')}
                  className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                    selectedCrop === 'soybean'
                      ? 'bg-green-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🌱 Soybean
                </button>
              </div>
            </div>

            {/* Image Upload Area */}
            <div className="mb-6">
              <label
                htmlFor="image-upload"
                className="block w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
              >
                {imagePreview ? (
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="max-h-64 mx-auto rounded-lg"
                  />
                ) : (
                  <div className="text-gray-500">
                    <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-lg font-medium">Click to upload image</p>
                    <p className="text-sm mt-2">PNG, JPG up to 10MB</p>
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
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600 shadow-lg'
              }`}
            >
              {analyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  Analyzing...
                </span>
              ) : (
                'Analyze Crop Health'
              )}
            </button>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <p className="font-medium">Error:</p>
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Right Panel - Results */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-green-600" />
              Analysis Results
            </h2>

            {analysisResult ? (
              <div className="space-y-6">
                {/* Overall Health */}
                <div className="bg-gradient-to-br from-blue-50 to-green-50 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-700">Overall Health</h3>
                    {getHealthIcon(analysisResult.report.status)}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-5xl font-bold ${getHealthColor(analysisResult.report.overall_health)}`}>
                      {analysisResult.report.overall_health.toFixed(1)}%
                    </span>
                    <span className="text-xl text-gray-600">
                      {analysisResult.report.status}
                    </span>
                  </div>
                </div>

                {/* Disease Summary */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-3">Disease Detection</h3>
                  <div className="space-y-2">
                    {Object.entries(analysisResult.report.disease_summary).map(([disease, count]) => (
                      <div key={disease} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium capitalize">{disease.replace(/_/g, ' ')}</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                          disease === 'healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {count} detected
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Damage Statistics */}
                {analysisResult.report.damaged_area_stats && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Damage Analysis</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-orange-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Damaged Areas</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {analysisResult.report.damaged_area_stats.total_damaged_areas}
                        </p>
                      </div>
                      <div className="bg-red-50 rounded-lg p-4">
                        <p className="text-sm text-gray-600">Damage %</p>
                        <p className="text-2xl font-bold text-red-600">
                          {analysisResult.report.damaged_area_stats.damage_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {analysisResult.report.recommendations && analysisResult.report.recommendations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Recommendations</h3>
                    <div className="space-y-2">
                      {analysisResult.report.recommendations.map((rec, idx) => (
                        <div key={idx} className="flex gap-2 p-3 bg-blue-50 rounded-lg">
                          <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-gray-700">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Visualizations */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-3">Health Visualizations</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {analysisResult.visualizations.health_map && (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">Health Map</p>
                        <img
                          src={`data:image/jpeg;base64,${analysisResult.visualizations.health_map}`}
                          alt="Health Map"
                          className="w-full rounded-lg border-2 border-gray-200"
                        />
                      </div>
                    )}
                    {analysisResult.visualizations.contour_map && (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">Contour Map</p>
                        <img
                          src={`data:image/jpeg;base64,${analysisResult.visualizations.contour_map}`}
                          alt="Contour Map"
                          className="w-full rounded-lg border-2 border-gray-200"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <Leaf className="w-16 h-16 mb-4" />
                <p className="text-lg">Upload and analyze an image to see results</p>
              </div>
            )}
          </div>
        </div>

        {/* Disease Info Cards */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Detectable Diseases</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Apple Diseases */}
            <div>
              <h3 className="text-xl font-semibold mb-3 text-red-600">🍎 Apple Diseases</h3>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 p-2 bg-green-50 rounded">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Healthy</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Apple Scab</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Black Rot</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Cedar Apple Rust</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Powdery Mildew</span>
                </li>
              </ul>
            </div>

            {/* Soybean Diseases */}
            <div>
              <h3 className="text-xl font-semibold mb-3 text-green-600">🌱 Soybean Diseases</h3>
              <ul className="space-y-2">
                <li className="flex items-center gap-2 p-2 bg-green-50 rounded">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Healthy</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Bacterial Blight</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Caterpillar</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Diabrotica Speciosa</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Downy Mildew</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Mosaic Virus</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Powdery Mildew</span>
                </li>
                <li className="flex items-center gap-2 p-2 bg-red-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span>Rust</span>
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
