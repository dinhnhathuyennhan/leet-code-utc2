// lib/axios.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { tokenStore } from "./token-store";

const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // BẮT BUỘC — để trình duyệt tự gửi cookie chứa refresh token
});

// Request interceptor — gắn access token từ memory
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStore.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — refresh khi 401
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];
const REFRESH_EXEMPT_PATHS = new Set(["/auth/login", "/auth/change-password"]);

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 &&
      !originalRequest._retry &&
      !REFRESH_EXEMPT_PATHS.has(originalRequest.url ?? "")) {
      // Nếu đang có 1 request refresh chạy rồi, các request khác chờ chung kết quả
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(axiosInstance(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Không cần gửi refreshToken trong body — cookie tự đi kèm nhờ withCredentials
        const { data } = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh-access-token`,
          {},
          { withCredentials: true }
        );

        tokenStore.setAccessToken(data.access_token);
        onRefreshed(data.access_token);
        isRefreshing = false;

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        tokenStore.clear();
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- axios.ts là module thuần, không phải component nên không gọi được useRouter(); cố ý full-reload để xoá sạch state client khi session hết hạn
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
