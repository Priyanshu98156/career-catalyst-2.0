import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'default_tenant',
    'X-User-ID': 'default_user',
  },
});

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

// API methods
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
