# Frontend Current Plan - Hybrid Model Strategy Dashboard

## Overview
Implementation of frontend dashboard for monitoring and managing the hybrid model strategy, providing real-time insights into model performance, costs, and escalation patterns.

## Dashboard Components

### 1. Model Performance Dashboard
```typescript
// services/console/src/components/dashboard/ModelPerformanceDashboard.tsx
interface ModelPerformanceData {
  model: string;
  role: string;
  avgResponseTime: number;
  successRate: number;
  totalRequests: number;
  costPerRequest: number;
  qualityScore: number;
}

const ModelPerformanceDashboard: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<ModelPerformanceData[]>([]);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h');

  useEffect(() => {
    const fetchPerformanceData = async () => {
      const response = await fetch(`/api/v1/monitoring/model-performance?range=${timeRange}`);
      const data = await response.json();
      setPerformanceData(data);
    };

    fetchPerformanceData();
    const interval = setInterval(fetchPerformanceData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [timeRange]);

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Model Performance</h2>
        <Select value={timeRange} onValueChange={(value) => setTimeRange(value as any)}>
          <SelectItem value="24h">Last 24 Hours</SelectItem>
          <SelectItem value="7d">Last 7 Days</SelectItem>
          <SelectItem value="30d">Last 30 Days</SelectItem>
        </Select>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={performanceData}>
          <XAxis dataKey="model" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="avgResponseTime" fill="#8884d8" name="Avg Response Time (ms)" />
          <Bar dataKey="successRate" fill="#82ca9d" name="Success Rate (%)" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};
```

### 2. Cost Analysis Dashboard
```typescript
// services/console/src/components/dashboard/CostAnalysisDashboard.tsx
interface CostData {
  model: string;
  totalCost: number;
  requestCount: number;
  avgCostPerRequest: number;
  projectedMonthly: number;
  savingsVsPrevious: number;
}

const CostAnalysisDashboard: React.FC = () => {
  const [costData, setCostData] = useState<CostData[]>([]);
  const [budget, setBudget] = useState<number>(1000);

  useEffect(() => {
    const fetchCostData = async () => {
      const response = await fetch('/api/v1/monitoring/cost-analysis');
      const data = await response.json();
      setCostData(data);
    };

    fetchCostData();
  }, []);

  const totalCost = costData.reduce((sum, item) => sum + item.totalCost, 0);
  const totalSavings = costData.reduce((sum, item) => sum + item.savingsVsPrevious, 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">${totalCost.toFixed(2)}</div>
          <p className="text-xs text-muted-foreground">
            vs ${budget.toFixed(2)} budget
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Savings</CardTitle>
          <TrendingDown className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">${totalSavings.toFixed(2)}</div>
          <p className="text-xs text-muted-foreground">
            vs previous configuration
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">GLM-4.5 Usage</CardTitle>
          <Brain className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {((costData.find(d => d.model === 'glm-4.5')?.requestCount || 0) / 
              costData.reduce((sum, d) => sum + d.requestCount, 0) * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            of all requests
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Escalation Rate</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {((costData.find(d => d.model === 'claude-4.1-opus')?.requestCount || 0) / 
              costData.reduce((sum, d) => sum + d.requestCount, 0) * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            to Claude 4.1 Opus
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
```

### 3. Escalation Management Interface
```typescript
// services/console/src/components/dashboard/EscalationManagement.tsx
interface EscalationRequest {
  id: string;
  taskType: string;
  reason: string;
  impactScope: string;
  requestedBy: string;
  timestamp: string;
  status: 'pending' | 'approved' | 'rejected';
  approvedBy?: string;
  decisionReason?: string;
}

const EscalationManagement: React.FC = () => {
  const [escalations, setEscalations] = useState<EscalationRequest[]>([]);
  const [selectedEscalation, setSelectedEscalation] = useState<EscalationRequest | null>(null);

  useEffect(() => {
    const fetchEscalations = async () => {
      const response = await fetch('/api/v1/config/models/escalations');
      const data = await response.json();
      setEscalations(data);
    };

    fetchEscalations();
  }, []);

  const handleEscalationDecision = async (escalationId: string, approved: boolean, reason: string) => {
    await fetch(`/api/v1/config/models/escalations/${escalationId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, reason })
    });
    
    // Refresh the list
    const response = await fetch('/api/v1/config/models/escalations');
    const data = await response.json();
    setEscalations(data);
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Escalation Management</h2>
      
      <Tabs defaultValue="pending" className="w-full">
        <TabsList>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="approved">Approved</TabsTrigger>
          <TabsTrigger value="rejected">Rejected</TabsTrigger>
        </TabsList>
        
        <TabsContent value="pending" className="space-y-4">
          {escalations.filter(e => e.status === 'pending').map(escalation => (
            <Card key={escalation.id} className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium">{escalation.taskType}</h3>
                  <p className="text-sm text-muted-foreground">{escalation.reason}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Impact: {escalation.impactScope} | Requested by: {escalation.requestedBy}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleEscalationDecision(escalation.id, true, 'Critical decision approved')}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEscalationDecision(escalation.id, false, 'Escalation not justified')}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </Card>
  );
};
```

### 4. Real-time Alert System
```typescript
// services/console/src/components/dashboard/AlertSystem.tsx
interface Alert {
  id: string;
  type: 'performance' | 'cost' | 'quality' | 'escalation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
}

const AlertSystem: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time alerts
    const websocket = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/alerts`);
    setWs(websocket);

    websocket.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      setAlerts(prev => [alert, ...prev]);
    };

    return () => websocket.close();
  }, []);

  const acknowledgeAlert = async (alertId: string) => {
    await fetch(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
      method: 'POST'
    });
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Real-time Alerts</h2>
        <Badge variant="outline" className="ml-2">
          {alerts.filter(a => !a.acknowledged).length} Unacknowledged
        </Badge>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.map(alert => (
          <div
            key={alert.id}
            className={`p-3 rounded-lg border-l-4 ${
              alert.acknowledged ? 'opacity-60' : ''
            }`}
            style={{ borderLeftColor: getSeverityColor(alert.severity).replace('bg-', '#') }}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={getSeverityColor(alert.severity)}>
                    {alert.severity}
                  </Badge>
                  <Badge variant="outline">{alert.type}</Badge>
                </div>
                <p className="text-sm">{alert.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
              {!alert.acknowledged && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => acknowledgeAlert(alert.id)}
                >
                  Acknowledge
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
```

### 5. Configuration Management
```typescript
// services/console/src/components/dashboard/ConfigurationManagement.tsx
const ConfigurationManagement: React.FC = () => {
  const [config, setConfig] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState<any>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      const response = await fetch('/api/v1/config/models');
      const data = await response.json();
      setConfig(data);
      setEditedConfig(data);
    };

    fetchConfig();
  }, []);

  const saveConfig = async () => {
    await fetch('/api/v1/config/models', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editedConfig)
    });
    setConfig(editedConfig);
    setIsEditing(false);
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Model Configuration</h2>
        {isEditing ? (
          <div className="flex gap-2">
            <Button onClick={saveConfig}>Save Changes</Button>
            <Button variant="outline" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button onClick={() => setIsEditing(true)}>Edit Configuration</Button>
        )}
      </div>

      {config && (
        <div className="space-y-4">
          {Object.entries(config.roles).map(([role, roleConfig]: [string, any]) => (
            <div key={role} className="border rounded-lg p-4">
              <h3 className="font-medium mb-2 capitalize">{role}</h3>
              {isEditing ? (
                <div className="space-y-2">
                  <Select
                    value={editedConfig.roles[role].default}
                    onValueChange={(value) => setEditedConfig(prev => ({
                      ...prev,
                      roles: {
                        ...prev.roles,
                        [role]: {
                          ...prev.roles[role],
                          default: value
                        }
                      }
                    }))}
                  >
                    <SelectItem value="glm-4.5">GLM-4.5</SelectItem>
                    <SelectItem value="claude-4.1-opus">Claude 4.1 Opus</SelectItem>
                    <SelectItem value="openrouter/sonoma-sky-alpha">Sonoma Sky Alpha</SelectItem>
                  </Select>
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-sm">
                    <span className="font-medium">Default Model:</span> {roleConfig.default}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Fallback:</span> {roleConfig.fallback}
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Escalation Enabled:</span> 
                    {roleConfig.escalationEnabled ? ' Yes' : ' No'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
```

## API Routes

### 1. Model Performance API
```typescript
// services/console/src/app/api/monitoring/model-performance/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const range = searchParams.get('range') || '24h';

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_ADK_URL}/v1/monitoring/model-performance?range=${range}`);
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch performance data' }, { status: 500 });
  }
}
```

### 2. Cost Analysis API
```typescript
// services/console/src/app/api/monitoring/cost-analysis/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_ADK_URL}/v1/monitoring/cost-analysis`);
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch cost data' }, { status: 500 });
  }
}
```

### 3. Escalation Management API
```typescript
// services/console/src/app/api/config/models/escalations/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_ADK_URL}/v1/config/models/escalations`);
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch escalations' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_ADK_URL}/v1/config/models/escalate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create escalation' }, { status: 500 });
  }
}
```

## Testing Strategy

### 1. Component Testing
```typescript
// services/console/src/components/dashboard/__tests__/ModelPerformanceDashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ModelPerformanceDashboard } from '../ModelPerformanceDashboard';

jest.mock('next/router', () => ({
  useRouter() {
    return { route: '/', pathname: '/', query: {}, asPath: '/' };
  },
}));

describe('ModelPerformanceDashboard', () => {
  beforeEach(() => {
    // Mock API responses
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve([
          { model: 'glm-4.5', avgResponseTime: 1200, successRate: 98.5 },
          { model: 'claude-4.1-opus', avgResponseTime: 800, successRate: 99.2 }
        ])
      })
    ) as any;
  });

  it('renders model performance data', async () => {
    render(<ModelPerformanceDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Model Performance')).toBeInTheDocument();
      expect(screen.getByText('GLM-4.5')).toBeInTheDocument();
    });
  });
});
```

### 2. Integration Testing
```typescript
// services/console/src/components/dashboard/__tests__/CostAnalysisDashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { CostAnalysisDashboard } from '../CostAnalysisDashboard';

describe('CostAnalysisDashboard', () => {
  it('displays cost savings correctly', async () => {
    render(<CostAnalysisDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Savings')).toBeInTheDocument();
      expect(screen.getByText(/\$\d+\.\d{2}/)).toBeInTheDocument();
    });
  });
});
```

## Styling with Tailwind CSS

### 1. Dashboard Layout
```css
/* services/console/src/styles/dashboard.css */
.dashboard-grid {
  @apply grid grid-cols-1 lg:grid-cols-3 gap-6;
}

.metric-card {
  @apply bg-white rounded-lg shadow-sm border p-6;
}

.alert-item {
  @apply p-4 rounded-lg border-l-4 bg-white;
}

.escalation-card {
  @apply transition-all duration-200 hover:shadow-md;
}
```

### 2. Responsive Design
```typescript
// services/console/src/components/dashboard/DashboardLayout.tsx
const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Model Strategy Dashboard</h1>
            <div className="flex items-center space-x-4">
              <Badge variant="outline">GLM-4.5 Active</Badge>
              <Badge variant="outline" className="text-green-600">
                Operational
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {children}
        </div>
      </main>
    </div>
  );
};
```

## Acceptance Criteria

1. ✅ **Dashboard Functionality**: All dashboard components render correctly and display real-time data
2. ✅ **Real-time Updates**: WebSocket connection provides live alerts and updates
3. ✅ **Configuration Management**: Users can view and edit model configurations
4. ✅ **Escalation Management**: Escalation requests can be reviewed and approved/rejected
5. ✅ **Performance Monitoring**: Model performance metrics are displayed with historical trends
6. ✅ **Cost Analysis**: Cost savings and budget tracking are visualized
7. ✅ **Responsive Design**: Dashboard works on desktop, tablet, and mobile devices
8. ✅ **Testing**: All component and integration tests pass

## API Endpoints for Testing

```bash
# Test performance data
curl http://localhost:3000/api/monitoring/model-performance

# Test cost analysis
curl http://localhost:3000/api/monitoring/cost-analysis

# Test escalation management
curl -X POST http://localhost:3000/api/config/models/escalate \
  -H "Content-Type: application/json" \
  -d '{"task_type": "architectural_decision", "reason": "Multi-service impact", "impact_scope": "system-wide"}'
```

## Next Steps

1. **Week 1**: Implement core dashboard components
2. **Week 2**: Add real-time WebSocket functionality
3. **Week 3**: Implement escalation management interface
4. **Week 4**: Complete testing and documentation