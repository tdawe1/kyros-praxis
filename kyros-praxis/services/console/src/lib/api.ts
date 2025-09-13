import { ApiClient } from '@kyros-praxis/api-client'

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