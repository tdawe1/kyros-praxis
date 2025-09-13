// Simple API client wrapper
class ApiClient {
  private baseURL: string;
  
  constructor(config: { baseURL: string }) {
    this.baseURL = config.baseURL;
  }
  
  private async request(path: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${path}`;
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const headers = {
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    };
    
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  get(path: string) {
    return this.request(path, { method: 'GET' });
  }
  
  post(path: string, data: any, options?: RequestInit) {
    return this.request(path, {
      method: 'POST',
      body: data instanceof URLSearchParams ? data : JSON.stringify(data),
      headers: {
        'Content-Type': data instanceof URLSearchParams 
          ? 'application/x-www-form-urlencoded' 
          : 'application/json',
        ...options?.headers,
      },
    });
  }
  
  put(path: string, data: any) {
    return this.request(path, {
      method: 'PUT',
      body: JSON.stringify(data),
      headers: { 'Content-Type': 'application/json' },
    });
  }
  
  delete(path: string) {
    return this.request(path, { method: 'DELETE' });
  }
}

// Configure API client with base URL
const apiClient = new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
})

// Type-safe API methods
export const api = {
  // Health check
  health: () => apiClient.get('/utils/health-check'),
  
  // Jobs
  jobs: {
    list: () => apiClient.get('/jobs'),
    create: (data: any) => apiClient.post('/jobs', data),
    get: (id: string) => apiClient.get(`/jobs/${id}`),
    update: (id: string, data: any) => apiClient.put(`/jobs/${id}`, data),
    delete: (id: string) => apiClient.delete(`/jobs/${id}`),
  },
  
  // Tasks/Collab
  tasks: {
    list: () => apiClient.get('/collab'),
    create: (data: any) => apiClient.post('/collab', data),
    get: (id: string) => apiClient.get(`/collab/${id}`),
  },
  
  // Auth
  auth: {
    login: (credentials: { username: string; password: string }) => 
      apiClient.post('/auth/login', new URLSearchParams(credentials), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }),
  },
}

export default apiClient
