import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  tenant_id: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  tenant_id: string;
  user_id: string;
  user?: User;
}

// Token storage helpers
export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem('cc_access_token'),
  getRefreshToken: (): string | null => localStorage.getItem('cc_refresh_token'),
  getTenantId: (): string => localStorage.getItem('cc_tenant_id') || 'default_tenant',
  getUserId: (): string => localStorage.getItem('cc_user_id') || 'default_user',
  getUser: (): User | null => {
    const raw = localStorage.getItem('cc_user');
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  setTokens: (auth: AuthResponse) => {
    localStorage.setItem('cc_access_token', auth.access_token);
    localStorage.setItem('cc_refresh_token', auth.refresh_token);
    localStorage.setItem('cc_tenant_id', auth.tenant_id);
    localStorage.setItem('cc_user_id', auth.user_id);
    if (auth.user) {
      localStorage.setItem('cc_user', JSON.stringify(auth.user));
    }
  },
  clearTokens: () => {
    localStorage.removeItem('cc_access_token');
    localStorage.removeItem('cc_refresh_token');
    localStorage.removeItem('cc_tenant_id');
    localStorage.removeItem('cc_user_id');
    localStorage.removeItem('cc_user');
  },
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ---------------------------------------------------------------------------
// 1. Request Interceptor: Attach Access Token and Tenant Headers
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = tokenStorage.getAccessToken();
    const tenantId = tokenStorage.getTenantId();
    const userId = tokenStorage.getUserId();

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    config.headers['X-Tenant-ID'] = tenantId;
    config.headers['X-User-ID'] = userId;

    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// 2. Response Interceptor: Double Token Silent Refresh on 401 Unauthorized
// ---------------------------------------------------------------------------
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Check if error is 401 and request wasn't already retried
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/api/auth/login') &&
      !originalRequest.url?.includes('/api/auth/register') &&
      !originalRequest.url?.includes('/api/auth/refresh')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenStorage.getRefreshToken();
      if (!refreshToken) {
        tokenStorage.clearTokens();
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = response.data;
        localStorage.setItem('cc_access_token', access_token);
        localStorage.setItem('cc_refresh_token', refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        tokenStorage.clearTokens();
        window.dispatchEvent(new Event('cc_auth_logout'));
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Resume & Profile Domain Interfaces
// ---------------------------------------------------------------------------
export interface EducationItem {
  institution: string;
  degree: string;
  field_of_study?: string;
  start_year?: string;
  end_year?: string;
  gpa?: string;
}

export interface ParsedExperienceItem {
  company: string;
  role: string;
  duration?: string;
  location?: string;
  bullet_points: string[];
  skills_used: string[];
}

export interface ProjectItem {
  title: string;
  description?: string;
  technologies: string[];
  bullet_points: string[];
  link?: string;
}

export interface ParsedProfile {
  full_name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
  summary?: string;
  skills: string[];
  education: EducationItem[];
  experiences: ParsedExperienceItem[];
  projects: ProjectItem[];
  certifications: any[];
}

export interface MasterBullet {
  id?: string;
  bullet_text: string;
  skills_used: string[];
  category: string;
  project_name?: string;
  impact_metrics?: string;
}

export interface JDAnalysis {
  job_title: string;
  company?: string;
  primary_skills: string[];
  core_responsibilities: string[];
  keywords_to_target: string[];
  seniority_level?: string;
}

export interface SynthesizedExperience {
  company: string;
  role: string;
  duration?: string;
  location?: string;
  tailored_bullets: string[];
}

export interface TailoredResumeContent {
  candidate_name: string;
  contact_info: {
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    github?: string;
    portfolio?: string;
  };
  professional_summary: string;
  highlighted_skills: string[];
  experiences: SynthesizedExperience[];
  projects: any[];
  education: any[];
  certifications: any[];
}

export interface TailoredResumeResponse {
  id?: string;
  job_title: string;
  match_score?: number;
  matched_keywords: string[];
  missing_keywords: string[];
  structured_resume: TailoredResumeContent;
  latex_source?: string;
}

export interface ResumeHistoryItem {
  id: string;
  title: string;
  structured_content: TailoredResumeContent;
  raw_latex?: string;
  match_score?: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Auth API Endpoints
// ---------------------------------------------------------------------------
export async function registerUser(payload: {
  email: string;
  password: string;
  full_name?: string;
  tenant_id?: string;
}): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/api/auth/register', payload);
  tokenStorage.setTokens(response.data);
  return response.data;
}

export async function loginUser(payload: {
  email: string;
  password: string;
  tenant_id?: string;
}): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/api/auth/login', payload);
  tokenStorage.setTokens(response.data);
  return response.data;
}

export async function logoutUser(): Promise<void> {
  const refreshToken = tokenStorage.getRefreshToken();
  try {
    if (refreshToken) {
      await apiClient.post('/api/auth/logout', { refresh_token: refreshToken });
    }
  } catch (err) {
    // Graceful ignore
  } finally {
    tokenStorage.clearTokens();
    window.dispatchEvent(new Event('cc_auth_logout'));
  }
}

export async function fetchCurrentUser(): Promise<User | null> {
  try {
    const response = await apiClient.get<User>('/api/auth/me');
    return response.data;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Profile & Resume API Methods
// ---------------------------------------------------------------------------
export async function uploadResumePdf(file: File, saveToDb: boolean = true): Promise<ParsedProfile> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<ParsedProfile>(
    `/api/profile/upload-resume?save_to_db=${saveToDb}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

export async function fetchProfile(): Promise<ParsedProfile | null> {
  try {
    const response = await apiClient.get<ParsedProfile>('/api/profile');
    return response.data;
  } catch (err: any) {
    if (err.response?.status === 404) return null;
    throw err;
  }
}

export async function saveProfile(profile: Partial<ParsedProfile>): Promise<any> {
  const response = await apiClient.post('/api/profile/save', profile);
  return response.data;
}

export async function fetchMasterBullets(): Promise<MasterBullet[]> {
  try {
    const response = await apiClient.get<MasterBullet[]>('/api/profile/bullets');
    return response.data;
  } catch (err) {
    return [];
  }
}

export async function addMasterBullets(bullets: MasterBullet[]): Promise<MasterBullet[]> {
  const response = await apiClient.post<MasterBullet[]>('/api/profile/bullets', bullets);
  return response.data;
}

export async function analyzeJobDescription(jd: string, jobTitle?: string): Promise<JDAnalysis> {
  const response = await apiClient.post<JDAnalysis>('/api/resume/analyze-jd', {
    job_description: jd,
    job_title: jobTitle,
  });
  return response.data;
}

export async function tailorResume(
  jobDescription: string,
  targetJobTitle?: string,
  topKBullets: number = 8
): Promise<TailoredResumeResponse> {
  const response = await apiClient.post<TailoredResumeResponse>('/api/resume/tailor', {
    job_description: jobDescription,
    target_job_title: targetJobTitle,
    top_k_bullets: topKBullets,
  });
  return response.data;
}

export async function fetchResumeHistory(): Promise<ResumeHistoryItem[]> {
  try {
    const response = await apiClient.get<ResumeHistoryItem[]>('/api/resume/history');
    return response.data;
  } catch (err) {
    return [];
  }
}
