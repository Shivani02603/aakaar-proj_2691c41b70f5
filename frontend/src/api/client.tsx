import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterResponse {
  message: string;
}

export interface CurrentUserResponse {
  id: string;
  email: string;
}

export interface DocumentUploadResponse {
  id: string;
  name: string;
  status: string;
}

export interface DocumentListResponse {
  documents: Array<{
    id: string;
    name: string;
    status: string;
  }>;
}

export interface IngestDocumentsRequest {
  documentIds: string[];
}

export interface IngestDocumentsResponse {
  message: string;
}

export interface AIQueryRequest {
  query: string;
  sessionId: string;
}

export interface AIQueryResponse {
  answer: string;
}

export interface QueryListResponse {
  queries: Array<{
    id: string;
    query: string;
    answer: string;
  }>;
}

export const login = (data: LoginRequest) => api.post<LoginResponse>('/api/auth/login', data);

export const register = (data: RegisterRequest) => api.post<RegisterResponse>('/api/auth/register', data);

export const logout = () => api.post('/api/auth/logout');

export const getCurrentUser = () => api.get<CurrentUserResponse>('/api/auth/me');

export const uploadDocument = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<DocumentUploadResponse>('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const listDocuments = () => api.get<DocumentListResponse>('/api/documents');

export const ingestDocuments = (data: IngestDocumentsRequest) =>
  api.post<IngestDocumentsResponse>('/api/ai/ingest', data);

export const aiQuery = (data: AIQueryRequest) => api.post<AIQueryResponse>('/api/ai/query', data);

export const listQueries = () => api.get<QueryListResponse>('/api/ai/queries');