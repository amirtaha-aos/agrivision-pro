// src/api/imageProcessor.js
import axios from 'axios';
import { API_CONFIG } from './config';

export const appleCounterAPI = {
  // شمارش سیب‌ها در تصویر
  countApples: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(
      `${API_CONFIG.MAVLINK_API}/api/apple/count`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return res.data;
  },
};

export const imageAPI = {
  // تغییر مود پردازش: 'yolo' | 'cv' | 'both'
  setMode: async (mode) => {
    const res = await axios.post(`${API_CONFIG.IMAGE_API}/api/processing/mode`, { mode });
    return res.data;
  },

  // استارت دوربین روی backend
  startCamera: async (source = 0) => {
    const res = await axios.post(
      `${API_CONFIG.IMAGE_API}/api/camera/start`,
      null,
      { params: { source } }
    );
    return res.data;
  },

  // توقف دوربین
  stopCamera: async () => {
    const res = await axios.post(`${API_CONFIG.IMAGE_API}/api/camera/stop`);
    return res.data;
  },

  // گرفتن آمار YOLO (healthy / defective / total)
  getYOLOStats: async () => {
    const res = await axios.get(`${API_CONFIG.IMAGE_API}/api/stats/yolo`);
    return res.data;
  },

  // ریست کردن آمار
  resetStats: async () => {
    const res = await axios.post(`${API_CONFIG.IMAGE_API}/api/stats/reset`);
    return res.data;
  },

  // URL استریم ویدیو (برای <img src=...>)
  getStreamURL: () => `${API_CONFIG.IMAGE_API}/api/camera/stream`,
};
