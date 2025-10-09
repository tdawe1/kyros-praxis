// Simple API client wrapper
class ApiClient {
  private baseURL: string;
  
  constructor(config: { baseURL: string }) {
    this.baseURL = config.baseURL;
  }
  
  private async request(path: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${path}`;
    let token: string | null = null;
    if (typeof window !== 'undefined') {
      try {
        // Only use NextAuth session token - no localStorage fallback for security
        const { getSession } = await import('next-auth/react');
        const session: any = await getSession();
        token = session?.accessToken;
      } catch {
        // No fallback to localStorage - rely on NextAuth for secure token storage
        token = null;
      }
    }
    
    const headers = {
      ...options.headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    };
    
    // Use HTTPS in production
    const finalUrl = process.env.NODE_ENV === 'production' 
      ? url.replace('http://', 'https://') 
      : url;
    
    const response = await fetch(finalUrl, {
      ...options,
      headers,
      credentials: 'include',
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
    updateStatus: (id: string, status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled') =>
      apiClient.put(`/jobs/${id}/status?status=${encodeURIComponent(status)}`, {}),
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
