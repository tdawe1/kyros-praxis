export interface Job {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  spec?: any;
}

export interface CoordinateEvent {
  event_type: string;
  agent_id: string;
  payload: Record<string, string>;
  timestamp: number;
}

export interface AuthToken {
  iss: string;
  aud: string;
  sub: string;
  exp: number;
  iat: number;
}

export interface ServiceHealth {
  service: string;
  status: 'healthy' | 'unhealthy';
  timestamp: number;
}

export interface Injectable {
  // Marker interface for injectable classes
}