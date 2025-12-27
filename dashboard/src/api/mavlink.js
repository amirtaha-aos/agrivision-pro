import axios from 'axios';
import { API_CONFIG } from './config';

export const mavlinkAPI = {
  // اتصال به کنترلر (فعلاً فقط لازم می‌شه وقتی خواستیم واقعا وصل شیم)
  connect: async (connectionString = '/dev/ttyACM0', baud = 57600) => {
    const response = await axios.post(
      `${API_CONFIG.MAVLINK_API}/api/connection/connect`,
      null,
      { params: { connection_string: connectionString, baud } }
    );
    return response.data;
  },

  disconnect: async () => {
    const response = await axios.post(`${API_CONFIG.MAVLINK_API}/api/connection/disconnect`);
    return response.data;
  },

  getStatus: async () => {
    const response = await axios.get(`${API_CONFIG.MAVLINK_API}/api/connection/status`);
    return response.data;
  },

  // گرفتن تله‌متری (بعداً برای دیباگ به درد می‌خوره)
  getTelemetry: async () => {
    const response = await axios.get(`${API_CONFIG.MAVLINK_API}/api/telemetry`);
    return response.data;
  },

  // کنترل پرواز (اینها رو بعداً به دکمه‌ها وصل می‌کنیم)
  arm: async () => {
    const response = await axios.post(`${API_CONFIG.MAVLINK_API}/api/flight/arm`);
    return response.data;
  },

  disarm: async () => {
    const response = await axios.post(`${API_CONFIG.MAVLINK_API}/api/flight/disarm`);
    return response.data;
  },

  takeoff: async (altitude) => {
    const response = await axios.post(
      `${API_CONFIG.MAVLINK_API}/api/flight/takeoff`,
      null,
      { params: { altitude } }
    );
    return response.data;
  },

  land: async () => {
    const response = await axios.post(`${API_CONFIG.MAVLINK_API}/api/flight/land`);
    return response.data;
  },

  returnToLaunch: async () => {
    const response = await axios.post(`${API_CONFIG.MAVLINK_API}/api/flight/rtl`);
    return response.data;
  },

  setMode: async (mode) => {
    const response = await axios.post(
      `${API_CONFIG.MAVLINK_API}/api/flight/mode`,
      null,
      { params: { mode } }
    );
    return response.data;
  },

  // 👉 مهم‌ترین چیزی که الان می‌خوایم: Mission Planning
  calculateMissionPlan: async (missionConfig) => {
    const response = await axios.post(
      `${API_CONFIG.MAVLINK_API}/api/mission/calculate`,
      missionConfig
    );
    return response.data;
  },
};
