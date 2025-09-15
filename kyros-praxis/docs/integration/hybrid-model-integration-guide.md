# Kyros Hybrid Model System - Integration Guide

## Table of Contents
- [Integration Overview](#integration-overview)
- [Getting Started with Integration](#getting-started-with-integration)
- [Authentication Setup](#authentication-setup)
- [Webhook Integration](#webhook-integration)
- [SDK Integration](#sdk-integration)
- [Third-Party Integrations](#third-party-integrations)
- [CI/CD Integration](#cicd-integration)
- [Monitoring Integration](#monitoring-integration)
- [Custom Agent Integration](#custom-agent-integration)
- [Best Practices](#best-practices)
- [Troubleshooting Integration Issues](#troubleshooting-integration-issues)

## Integration Overview

### Integration Types

Kyros supports several integration approaches:

1. **API Integration**: Direct REST API calls
2. **Webhook Integration**: Event-driven notifications
3. **SDK Integration**: Pre-built client libraries
4. **Third-Party Integration**: Connect with existing tools
5. **Custom Agent Integration**: Extend with custom AI agents
6. **CI/CD Integration**: Automate in development workflows

### Integration Benefits

- **Automated Workflows**: Streamline development processes
- **Real-time Monitoring**: Get instant notifications on task progress
- **Cost Optimization**: Integrate with existing cost tracking systems
- **Team Collaboration**: Connect with project management tools
- **Custom Extensions**: Add domain-specific functionality

### Integration Architecture

```
External System → Kyros API → Processing → Response → External System
     ↓                     ↓              ↓            ↓
  Authentication     Task Creation   Agent Work    Result Delivery
  Rate Limiting      Webhook Events  Model Usage   Status Updates
```

## Getting Started with Integration

### Prerequisites

Before integrating with Kyros, ensure you have:

1. **Kyros Account**: Active account with API access
2. **API Credentials**: Valid API key or OAuth2 credentials
3. **Development Environment**: Python 3.8+ or Node.js 16+
4. **Network Access**: Ability to make HTTPS requests
5. **Webhook Endpoint**: Publicly accessible URL for webhook delivery (optional)

### API Key Generation

1. Log in to your Kyros dashboard
2. Navigate to Settings → API Keys
3. Click "Generate New API Key"
4. Set key name and permissions
5. Copy and securely store the API key

### Basic Integration Setup

**Environment Configuration:**
```bash
# .env file
KYROS_API_URL="https://api.kyros.com/v1"
KYROS_API_KEY="your-api-key-here"
KYROS_WEBHOOK_SECRET="your-webhook-secret"
KYROS_ENVIRONMENT="production"
```

**Health Check:**
```bash
# Test API connectivity
curl -X GET "$KYROS_API_URL/monitoring/health" \
  -H "Authorization: Bearer $KYROS_API_KEY"
```

## Authentication Setup

### API Key Authentication

**Simple Request:**
```bash
curl -X GET "$KYROS_API_URL/tasks" \
  -H "Authorization: Bearer $KYROS_API_KEY"
```

**Python Example:**
```python
import requests
import os

api_key = os.getenv('KYROS_API_KEY')
base_url = os.getenv('KYROS_API_URL')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

response = requests.get(f'{base_url}/tasks', headers=headers)
tasks = response.json()
```

### OAuth2 Authentication

**Setup OAuth2 Application:**
1. In Kyros dashboard, navigate to Settings → OAuth2
2. Register your application
3. Note client ID and client secret
4. Configure redirect URIs

**Authorization Flow:**
```python
from authlib.integrations.requests_client import OAuth2Session

client_id = os.getenv('OAUTH2_CLIENT_ID')
client_secret = os.getenv('OAUTH2_CLIENT_SECRET')
redirect_uri = 'https://your-app.com/callback'

# Create OAuth2 session
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)

# Get authorization URL
authorization_url, state = oauth.authorization_url(
    'https://api.kyros.com/auth/oauth2/authorize'
)

# Redirect user to authorization_url
# After authorization, handle callback
token = oauth.fetch_token(
    'https://api.kyros.com/auth/oauth2/callback',
    authorization_response=request.url,
    client_secret=client_secret
)
```

### JWT Authentication

**Generate JWT Token:**
```python
import jwt
from datetime import datetime, timedelta

payload = {
    'user_id': 'user_123',
    'roles': ['developer'],
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow()
}

token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')
```

## Webhook Integration

### Webhook Configuration

**Create Webhook:**
```bash
curl -X POST "$KYROS_API_URL/webhooks" \
  -H "Authorization: Bearer $KYROS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/kyros",
    "events": ["task.created", "task.completed", "escalation.approved"],
    "secret": "your-webhook-secret"
  }'
```

### Webhook Handler Implementation

**Python Flask Example:**
```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = 'your-webhook-secret'

@app.route('/webhooks/kyros', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Kyros-Signature')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Process webhook event
    event = request.json
    event_type = event.get('type')
    data = event.get('data')
    
    if event_type == 'task.created':
        handle_task_created(data)
    elif event_type == 'task.completed':
        handle_task_completed(data)
    elif event_type == 'escalation.approved':
        handle_escalation_approved(data)
    
    return jsonify({'status': 'received'}), 200

def handle_task_created(task_data):
    print(f"New task created: {task_data['title']}")
    # Send notification to team
    # Update project management system
    # Log to analytics

def handle_task_completed(task_data):
    print(f"Task completed: {task_data['title']}")
    # Update project status
    # Send completion notification
    # Trigger downstream processes

def handle_escalation_approved(escalation_data):
    print(f"Escalation approved: {escalation_data['task_id']}")
    # Notify stakeholders
    # Update cost tracking
    # Log escalation metrics

if __name__ == '__main__':
    app.run(port=5000)
```

**Node.js Express Example:**
```javascript
const express = require('express');
const crypto = require('crypto');
const app = express();

app.use(express.json());

const WEBHOOK_SECRET = 'your-webhook-secret';

app.post('/webhooks/kyros', (req, res) => {
    const signature = req.headers['x-kyros-signature'];
    const payload = JSON.stringify(req.body);
    
    const expectedSignature = crypto
        .createHmac('sha256', WEBHOOK_SECRET)
        .update(payload)
        .digest('hex');
    
    if (signature !== expectedSignature) {
        return res.status(401).json({ error: 'Invalid signature' });
    }
    
    const { type, data } = req.body;
    
    switch (type) {
        case 'task.created':
            handleTaskCreated(data);
            break;
        case 'task.completed':
            handleTaskCompleted(data);
            break;
        case 'escalation.approved':
            handleEscalationApproved(data);
            break;
    }
    
    res.json({ status: 'received' });
});

function handleTaskCreated(task) {
    console.log(`New task created: ${task.title}`);
    // Integration logic here
}

function handleTaskCompleted(task) {
    console.log(`Task completed: ${task.title}`);
    // Integration logic here
}

function handleEscalationApproved(escalation) {
    console.log(`Escalation approved: ${escalation.task_id}`);
    // Integration logic here
}

app.listen(5000, () => {
    console.log('Webhook server running on port 5000');
});
```

### Webhook Events

**Task Events:**
- `task.created` - New task created
- `task.started` - Task processing started
- `task.progress` - Task progress update
- `task.completed` - Task completed successfully
- `task.failed` - Task failed
- `task.cancelled` - Task cancelled

**Escalation Events:**
- `escalation.requested` - Escalation requested
- `escalation.approved` - Escalation approved
- `escalation.rejected` - Escalation rejected
- `escalation.completed` - Escalation processing completed

**System Events:**
- `system.health_check` - System health status
- `system.alert` - System alert triggered
- `system.maintenance` - Maintenance mode status

## SDK Integration

### Python SDK

**Installation:**
```bash
pip install kyros-sdk
```

**Basic Usage:**
```python
from kyros import KyrosClient
from kyros.models import Task, AgentContext

# Initialize client
client = KyrosClient(
    api_key='your-api-key',
    base_url='https://api.kyros.com'
)

# Create a task
task = Task(
    title='Implement user authentication',
    description='Add JWT authentication with OAuth2 integration',
    type='implementation',
    priority='high',
    assignee_role='implementer',
    acceptance_criteria=[
        'Users can register with email/password',
        'OAuth2 integration works',
        'JWT tokens properly validated'
    ]
)

created_task = client.tasks.create(task)
print(f"Task created: {created_task.id}")

# Submit to agent
context = AgentContext(
    repository_state='main branch at abc123',
    recent_changes=[
        'feat: Added user model',
        'fix: Fixed authentication bug'
    ]
)

submission = client.agents.submit('implementer', created_task.id, context)
print(f"Task submitted: {submission.submission_id}")

# Monitor progress
while True:
    status = client.tasks.get_status(created_task.id)
    print(f"Status: {status.status} ({status.progress.percentage}%)")
    
    if status.status in ['completed', 'failed']:
        break
    
    time.sleep(30)

# Get cost analysis
costs = client.monitoring.get_costs(period='7d')
print(f"Total cost: ${costs.total_cost:.2f}")
print(f"Savings: ${costs.savings.vs_premium_only:.2f}")
```

### JavaScript SDK

**Installation:**
```bash
npm install @kyros/sdk
```

**Basic Usage:**
```javascript
import { KyrosClient, Task, AgentContext } from '@kyros/sdk';

// Initialize client
const client = new KyrosClient({
    apiKey: 'your-api-key',
    baseURL: 'https://api.kyros.com'
});

// Create a task
const task = new Task({
    title: 'Implement user authentication',
    description: 'Add JWT authentication with OAuth2 integration',
    type: 'implementation',
    priority: 'high',
    assignee_role: 'implementer',
    acceptance_criteria: [
        'Users can register with email/password',
        'OAuth2 integration works',
        'JWT tokens properly validated'
    ]
});

const createdTask = await client.tasks.create(task);
console.log(`Task created: ${createdTask.id}`);

// Submit to agent
const context = new AgentContext({
    repository_state: 'main branch at abc123',
    recent_changes: [
        'feat: Added user model',
        'fix: Fixed authentication bug'
    ]
});

const submission = await client.agents.submit('implementer', createdTask.id, context);
console.log(`Task submitted: ${submission.submissionId}`);

// Monitor progress
const monitorProgress = async () => {
    const status = await client.tasks.getStatus(createdTask.id);
    console.log(`Status: ${status.status} (${status.progress.percentage}%)`);
    
    if (status.status === 'completed' || status.status === 'failed') {
        return;
    }
    
    setTimeout(monitorProgress, 30000);
};

monitorProgress();

// Get cost analysis
const costs = await client.monitoring.getCosts({ period: '7d' });
console.log(`Total cost: $${costs.totalCost.toFixed(2)}`);
console.log(`Savings: $${costs.savings.vsPremiumOnly.toFixed(2)}`);
```

### Java SDK

**Installation (Maven):**
```xml
<dependency>
    <groupId>com.kyros</groupId>
    <artifactId>kyros-java-sdk</artifactId>
    <version>1.0.0</version>
</dependency>
```

**Basic Usage:**
```java
import com.kyros.sdk.*;
import com.kyros.sdk.models.*;

public class KyrosIntegration {
    public static void main(String[] args) {
        // Initialize client
        KyrosClient client = new KyrosClient.Builder()
            .apiKey("your-api-key")
            .baseUrl("https://api.kyros.com")
            .build();
        
        // Create task
        Task task = new Task.Builder()
            .title("Implement user authentication")
            .description("Add JWT authentication with OAuth2 integration")
            .type(Task.Type.IMPLEMENTATION)
            .priority(Task.Priority.HIGH)
            .assigneeRole("implementer")
            .addAcceptanceCriterion("Users can register with email/password")
            .addAcceptanceCriterion("OAuth2 integration works")
            .addAcceptanceCriterion("JWT tokens properly validated")
            .build();
        
        try {
            Task createdTask = client.tasks().create(task);
            System.out.println("Task created: " + createdTask.getId());
            
            // Submit to agent
            AgentContext context = new AgentContext.Builder()
                .repositoryState("main branch at abc123")
                .addRecentChange("feat: Added user model")
                .addRecentChange("fix: Fixed authentication bug")
                .build();
            
            AgentSubmission submission = client.agents()
                .submit("implementer", createdTask.getId(), context);
            System.out.println("Task submitted: " + submission.getSubmissionId());
            
            // Monitor progress
            while (true) {
                TaskStatus status = client.tasks().getStatus(createdTask.getId());
                System.out.printf("Status: %s (%.1f%%)%n", 
                    status.getStatus(), status.getProgress().getPercentage());
                
                if (status.getStatus() == TaskStatus.Status.COMPLETED ||
                    status.getStatus() == TaskStatus.Status.FAILED) {
                    break;
                }
                
                Thread.sleep(30000);
            }
            
            // Get cost analysis
            CostAnalysis costs = client.monitoring().getCosts(CostAnalysis.Period.WEEK);
            System.out.printf("Total cost: $%.2f%n", costs.getTotalCost());
            System.out.printf("Savings: $%.2f%n", costs.getSavings().getVsPremiumOnly());
            
        } catch (KyrosException e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

## Third-Party Integrations

### Jira Integration

**Jira Webhook Handler:**
```python
import requests
import json

class JiraIntegration:
    def __init__(self, jira_url, jira_token, kyros_api_key):
        self.jira_url = jira_url.rstrip('/')
        self.jira_token = jira_token
        self.kyros_api_key = kyros_api_key
        self.kyros_base_url = 'https://api.kyros.com/v1'
        
        self.jira_headers = {
            'Authorization': f'Basic {jira_token}',
            'Content-Type': 'application/json'
        }
        
        self.kyros_headers = {
            'Authorization': f'Bearer {kyros_api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_jira_issue(self, task_data):
        """Create Jira issue from Kyros task"""
        issue_data = {
            'fields': {
                'project': {'key': 'DEV'},
                'summary': task_data['title'],
                'description': task_data['description'],
                'issuetype': {'name': 'Task'},
                'priority': {'name': task_data['priority'].title()},
                'labels': ['kyros', task_data['type']]
            }
        }
        
        response = requests.post(
            f'{self.jira_url}/rest/api/2/issue',
            headers=self.jira_headers,
            json=issue_data
        )
        
        if response.status_code == 201:
            issue_data = response.json()
            return issue_data['key']
        return None
    
    def update_jira_status(self, task_id, status):
        """Update Jira issue status based on Kyros task status"""
        # Map Kyros status to Jira status
        status_map = {
            'pending': 'To Do',
            'in_progress': 'In Progress',
            'completed': 'Done',
            'failed': 'Blocked'
        }
        
        jira_status = status_map.get(status, 'To Do')
        
        transition_data = {
            'transition': {'name': jira_status}
        }
        
        # Assuming we have the Jira issue key stored
        issue_key = self.get_jira_issue_key(task_id)
        if issue_key:
            requests.post(
                f'{self.jira_url}/rest/api/2/issue/{issue_key}/transitions',
                headers=self.jira_headers,
                json=transition_data
            )
    
    def get_jira_issue_key(self, task_id):
        """Retrieve Jira issue key for Kyros task"""
        # This would typically be stored in a mapping table
        # For demo purposes, we'll return a mock key
        return f"KYROS-{task_id.split('_')[1]}"

# Usage
jira_integration = JiraIntegration(
    jira_url='https://your-company.atlassian.net',
    jira_token='base64-encoded-token',
    kyros_api_key='your-kyros-api-key'
)

# Handle Kyros webhook events
@app.route('/webhooks/kyros', methods=['POST'])
def handle_kyros_webhook():
    event = request.json
    event_type = event.get('type')
    data = event.get('data')
    
    if event_type == 'task.created':
        # Create corresponding Jira issue
        jira_key = jira_integration.create_jira_issue(data)
        # Store mapping between Kyros task and Jira issue
        
    elif event_type in ['task.completed', 'task.failed']:
        # Update Jira issue status
        jira_integration.update_jira_status(data['id'], data['status'])
    
    return jsonify({'status': 'processed'})
```

### Slack Integration

**Slack Bot Integration:**
```javascript
const { WebClient } = require('@slack/web-api');
const kyros = require('@kyros/sdk');

class SlackBot {
    constructor(slackToken, kyrosApiKey) {
        this.slack = new WebClient(slackToken);
        this.kyros = new KyrosClient({ apiKey: kyrosApiKey });
        this.channel = '#kyros-notifications';
    }
    
    async sendTaskNotification(task, message) {
        const blocks = [
            {
                type: 'header',
                text: {
                    type: 'plain_text',
                    text: `Kyros Task: ${task.title}`
                }
            },
            {
                type: 'section',
                text: {
                    type: 'mrkdwn',
                    text: `*Description:* ${task.description}\n` +
                           `*Status:* ${task.status}\n` +
                           `*Priority:* ${task.priority}\n` +
                           `*Assigned to:* ${task.assignee_role}`
                }
            },
            {
                type: 'actions',
                elements: [
                    {
                        type: 'button',
                        text: { type: 'plain_text', text: 'View Details' },
                        url: `https://kyros.com/tasks/${task.id}`,
                        style: 'primary'
                    },
                    {
                        type: 'button',
                        text: { type: 'plain_text', text: 'Request Escalation' },
                        action_id: 'request_escalation',
                        value: task.id
                    }
                ]
            }
        ];
        
        await this.slack.chat.postMessage({
            channel: this.channel,
            text: message,
            blocks: blocks
        });
    }
    
    async handleEscalationRequest(action) {
        const taskId = action.value;
        
        try {
            const escalation = await this.kyros.escalations.submit({
                task_id: taskId,
                reason: 'Requested via Slack',
                priority: 'high'
            });
            
            await this.slack.chat.postMessage({
                channel: this.channel,
                text: `Escalation requested for task ${taskId}. Status: ${escalation.status}`
            });
        } catch (error) {
            await this.slack.chat.postMessage({
                channel: this.channel,
                text: `Failed to request escalation: ${error.message}`
            });
        }
    }
    
    async sendDailyReport() {
        const costs = await this.kyros.monitoring.getCosts({ period: '1d' });
        const metrics = await this.kyros.monitoring.getMetrics({ period: '1d' });
        
        const blocks = [
            {
                type: 'header',
                text: {
                    type: 'plain_text',
                    text: '📊 Kyros Daily Report'
                }
            },
            {
                type: 'section',
                fields: [
                    {
                        type: 'mrkdwn',
                        text: `*Total Cost:*\n$${costs.totalCost.toFixed(2)}`
                    },
                    {
                        type: 'mrkdwn',
                        text: `*Tasks Completed:*\n${metrics.taskCompletionRate.average}`
                    },
                    {
                        type: 'mrkdwn',
                        text: `*Success Rate:*\n${metrics.averageResponseTime.average}s`
                    },
                    {
                        type: 'mrkdwn',
                        text: `*Savings:*\n$${costs.savings.vsPremiumOnly.toFixed(2)}`
                    }
                ]
            }
        ];
        
        await this.slack.chat.postMessage({
            channel: this.channel,
            blocks: blocks
        });
    }
}

// Usage
const slackBot = new SlackBot('slack-bot-token', 'kyros-api-key');

// Handle Slack slash commands
app.post('/slack/commands', async (req, res) => {
    const { command, text } = req.body;
    
    if (command === '/kyros-status') {
        const health = await slackBot.kyros.monitoring.getHealth();
        await res.json({
            response_type: 'ephemeral',
            text: `Kyros Status: ${health.overall_status}`
        });
    }
    
    if (command === '/kyros-costs') {
        const costs = await slackBot.kyros.monitoring.getCosts({ period: '1d' });
        await res.json({
            response_type: 'ephemeral',
            text: `Daily costs: $${costs.totalCost.toFixed(2)}`
        });
    }
});
```

### GitHub Integration

**GitHub Actions Integration:**
```yaml
name: Kyros Integration
on:
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, synchronize]

jobs:
  create-kyros-task:
    runs-on: ubuntu-latest
    steps:
      - name: Create Kyros Task
        uses: kyros/kyros-github-action@v1
        with:
          api-key: ${{ secrets.KYROS_API_KEY }}
          action: create-task
          title: "${{ github.event.issue.title || github.event.pull_request.title }}"
          description: "${{ github.event.issue.body || github.event.pull_request.body }}"
          assignee-role: "implementer"
          priority: "medium"
          
      - name: Add Comment
        uses: actions/github-script@v6
        with:
          script: |
            const taskId = steps.create-kyros-task.outputs.task-id;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🤖 Kyros task created: Task ID ${taskId}`
            });
```

**GitHub Webhook Integration:**
```python
import requests
import json

class GitHubIntegration:
    def __init__(self, github_token, kyros_api_key):
        self.github_token = github_token
        self.kyros_api_key = kyros_api_key
        
        self.github_headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        self.kyros_headers = {
            'Authorization': f'Bearer {kyros_api_key}',
            'Content-Type': 'application/json'
        }
    
    def handle_issue_event(self, event):
        """Handle GitHub issue events"""
        if event.get('action') == 'opened':
            issue = event.get('issue')
            
            # Create Kyros task from issue
            task_data = {
                'title': issue['title'],
                'description': issue['body'],
                'type': 'implementation',
                'priority': self.map_priority(issue['labels']),
                'assignee_role': 'implementer',
                'metadata': {
                    'github_issue_id': issue['id'],
                    'github_issue_number': issue['number']
                }
            }
            
            response = requests.post(
                'https://api.kyros.com/v1/tasks',
                headers=self.kyros_headers,
                json=task_data
            )
            
            if response.status_code == 201:
                task = response.json()['data']
                
                # Add comment to GitHub issue
                self.add_issue_comment(
                    issue['number'],
                    f'🤖 Kyros task created: {task["id"]}'
                )
                
                # Store mapping
                self.store_task_mapping(task['id'], issue['id'])
    
    def handle_pr_event(self, event):
        """Handle GitHub pull request events"""
        if event.get('action') in ['opened', 'synchronize']:
            pr = event.get('pull_request')
            
            # Create review task for Critic
            task_data = {
                'title': f'Review PR: {pr["title"]}',
                'description': f'Review pull request #{pr["number"]}',
                'type': 'review',
                'priority': 'high',
                'assignee_role': 'critic',
                'metadata': {
                    'github_pr_id': pr['id'],
                    'github_pr_number': pr['number'],
                    'pr_url': pr['html_url']
                }
            }
            
            response = requests.post(
                'https://api.kyros.com/v1/tasks',
                headers=self.kyros_headers,
                json=task_data
            )
            
            if response.status_code == 201:
                task = response.json()['data']
                
                # Add comment to PR
                self.add_pr_comment(
                    pr['number'],
                    f'🤖 Kyros review task created: {task["id"]}'
                )
    
    def map_priority(self, labels):
        """Map GitHub labels to Kyros priority"""
        priority_map = {
            'critical': 'critical',
            'high': 'high',
            'priority-high': 'high',
            'medium': 'medium',
            'priority-medium': 'medium',
            'low': 'low',
            'priority-low': 'low'
        }
        
        for label in labels:
            if label['name'] in priority_map:
                return priority_map[label['name']]
        
        return 'medium'
    
    def add_issue_comment(self, issue_number, comment):
        """Add comment to GitHub issue"""
        # Implementation depends on your GitHub API integration
        pass
    
    def add_pr_comment(self, pr_number, comment):
        """Add comment to GitHub pull request"""
        # Implementation depends on your GitHub API integration
        pass
```

## CI/CD Integration

### GitHub Actions Integration

**Kyros Task in CI/CD Pipeline:**
```yaml
name: Deploy with Kyros
on:
  push:
    branches: [main]

jobs:
  create-deployment-task:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Create deployment task
        id: create-task
        uses: kyros/create-task-action@v1
        with:
          api-key: ${{ secrets.KYROS_API_KEY }}
          title: "Deploy ${{ github.sha }} to production"
          description: "Deploy commit ${{ github.sha }} to production environment"
          type: "deployment"
          priority: "high"
          assignee-role: "integrator"
          metadata: '{"commit": "${{ github.sha }}", "environment": "production"}'
      
      - name: Wait for task completion
        uses: kyros/wait-task-action@v1
        with:
          api-key: ${{ secrets.KYROS_API_KEY }}
          task-id: ${{ steps.create-task.outputs.task-id }}
          timeout: 1800
      
      - name: Get task results
        id: get-results
        uses: kyros/get-task-action@v1
        with:
          api-key: ${{ secrets.KYROS_API_KEY }}
          task-id: ${{ steps.create-task.outputs.task-id }}
      
      - name: Deploy
        run: |
          echo "Deploying based on Kyros task results..."
          # Your deployment logic here
          echo "Task status: ${{ steps.get-results.outputs.status }}"
```

### Jenkins Integration

**Jenkins Pipeline:**
```groovy
pipeline {
    agent any
    environment {
        KYROS_API_KEY = credentials('kyros-api-key')
    }
    
    stages {
        stage('Create Kyros Task') {
            steps {
                script {
                    def taskData = [
                        title: "Build and deploy ${env.BUILD_ID}",
                        description: "Build application and deploy to production",
                        type: "deployment",
                        priority: "high",
                        assignee_role: "integrator",
                        metadata: [
                            build_id: env.BUILD_ID,
                            commit: env.GIT_COMMIT
                        ]
                    ]
                    
                    def response = sh(
                        script: """
                            curl -X POST "https://api.kyros.com/v1/tasks" \
                            -H "Authorization: Bearer ${KYROS_API_KEY}" \
                            -H "Content-Type: application/json" \
                            -d '${groovy.json.JsonOutput.toJson(taskData)}'
                        """,
                        returnStdout: true
                    )
                    
                    def task = readJSON text: response
                    env.KYROS_TASK_ID = task.data.id
                }
            }
        }
        
        stage('Wait for Task Completion') {
            steps {
                script {
                    timeout(time: 30, unit: 'MINUTES') {
                        while (true) {
                            def response = sh(
                                script: """
                                    curl -X GET "https://api.kyros.com/v1/tasks/${env.KYROS_TASK_ID}" \
                                    -H "Authorization: Bearer ${KYROS_API_KEY}"
                                """,
                                returnStdout: true
                            )
                            
                            def task = readJSON text: response
                            
                            if (task.data.status in ['completed', 'failed']) {
                                break
                            }
                            
                            sleep(time: 30, unit: 'SECONDS')
                        }
                    }
                }
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    def response = sh(
                        script: """
                            curl -X GET "https://api.kyros.com/v1/tasks/${env.KYROS_TASK_ID}" \
                            -H "Authorization: Bearer ${KYROS_API_KEY}"
                        """,
                        returnStdout: true
                    )
                    
                    def task = readJSON text: response
                    
                    if (task.data.status == 'completed') {
                        echo "Deploying based on Kyros task approval..."
                        // Your deployment logic here
                    } else {
                        error "Kyros task failed: ${task.data.error}"
                    }
                }
            }
        }
    }
}
```

### GitLab CI Integration

**GitLab CI Configuration:**
```yaml
stages:
  - create-task
  - wait-approval
  - deploy

create-kyros-task:
  stage: create-task
  script:
    - |
      curl -X POST "$KYROS_API_URL/tasks" \
        -H "Authorization: Bearer $KYROS_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
          \"title\": \"Deploy $CI_COMMIT_SHA to production\",
          \"description\": \"Deploy commit $CI_COMMIT_SHA to production environment\",
          \"type\": \"deployment\",
          \"priority\": \"high\",
          \"assignee_role\": \"integrator\",
          \"metadata\": {
            \"commit\": \"$CI_COMMIT_SHA\",
            \"environment\": \"production\",
            \"pipeline_id\": \"$CI_PIPELINE_ID\"
          }
        }" > task_response.json
    
    - echo "TASK_ID=$(jq -r '.data.id' task_response.json)" >> task.env
  artifacts:
    reports:
      dotenv: task.env

wait-kyros-approval:
  stage: wait-approval
  script:
    - |
      while true; do
        response=$(curl -X GET "$KYROS_API_URL/tasks/$TASK_ID" \
          -H "Authorization: Bearer $KYROS_API_KEY")
        
        status=$(echo $response | jq -r '.data.status')
        
        if [[ "$status" == "completed" || "$status" == "failed" ]]; then
          break
        fi
        
        sleep 30
      done
    
    - echo $response > task_status.json
  artifacts:
    paths:
      - task_status.json

deploy-production:
  stage: deploy
  script:
    - |
      status=$(jq -r '.data.status' task_status.json)
      
      if [[ "$status" == "completed" ]]; then
        echo "Deploying to production..."
        # Your deployment commands here
      else
        echo "Deployment rejected by Kyros task"
        exit 1
      fi
  only:
    - main
```

## Monitoring Integration

### Prometheus Integration

**Kyros Metrics Exporter:**
```python
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import requests
import threading

class KyrosMetricsExporter:
    def __init__(self, kyros_api_key):
        self.kyros_api_key = kyros_api_key
        self.headers = {'Authorization': f'Bearer {kyros_api_key}'}
        
        # Define Prometheus metrics
        self.task_completion_rate = Gauge(
            'kyros_task_completion_rate',
            'Task completion rate percentage'
        )
        
        self.average_response_time = Gauge(
            'kyros_average_response_time_seconds',
            'Average response time in seconds'
        )
        
        self.daily_cost = Gauge(
            'kyros_daily_cost_dollars',
            'Daily cost in USD'
        )
        
        self.escalation_rate = Gauge(
            'kyros_escalation_rate_percentage',
            'Escalation rate percentage'
        )
        
        self.tasks_total = Counter(
            'kyros_tasks_total',
            'Total number of tasks',
            ['status', 'type']
        )
        
        self.model_usage_total = Counter(
            'kyros_model_usage_total',
            'Total model usage',
            ['model', 'role']
        )
    
    def collect_metrics(self):
        """Collect metrics from Kyros API"""
        try:
            # Get performance metrics
            response = requests.get(
                'https://api.kyros.com/v1/monitoring/metrics?period=1h',
                headers=self.headers
            )
            metrics = response.json()['data']['metrics']
            
            # Update Prometheus metrics
            self.task_completion_rate.set(metrics['task_completion_rate']['average'])
            self.average_response_time.set(metrics['average_response_time']['average'])
            self.escalation_rate.set(metrics['escalation_rate']['average'])
            
            # Get cost metrics
            cost_response = requests.get(
                'https://api.kyros.com/v1/monitoring/costs?period=1d',
                headers=self.headers
            )
            costs = cost_response.json()['data']
            self.daily_cost.set(costs['total_cost'])
            
            # Get task statistics
            tasks_response = requests.get(
                'https://api.kyros.com/v1/tasks?limit=100',
                headers=self.headers
            )
            tasks = tasks_response.json()['data']['tasks']
            
            for task in tasks:
                self.tasks_total.labels(
                    status=task['status'],
                    type=task['type']
                ).inc()
        
        except Exception as e:
            print(f"Error collecting metrics: {e}")
    
    def start_server(self, port=8000):
        """Start Prometheus metrics server"""
        start_http_server(port)
        
        # Start metrics collection thread
        def collect_loop():
            while True:
                self.collect_metrics()
                time.sleep(60)  # Collect every minute
        
        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()

# Usage
if __name__ == '__main__':
    exporter = KyrosMetricsExporter('your-kyros-api-key')
    exporter.start_server(port=8000)
    
    print("Prometheus metrics exporter running on port 8000")
    print("Metrics available at: http://localhost:8000/metrics")
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kyros'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'kyros-system'
    static_configs:
      - targets: ['kyros-orchestrator:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "Kyros Hybrid Model System",
    "panels": [
      {
        "title": "Task Completion Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "kyros_task_completion_rate",
            "legendFormat": "Completion Rate"
          }
        ]
      },
      {
        "title": "Average Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "kyros_average_response_time_seconds",
            "legendFormat": "Response Time"
          }
        ]
      },
      {
        "title": "Daily Cost",
        "type": "stat",
        "targets": [
          {
            "expr": "kyros_daily_cost_dollars",
            "legendFormat": "Daily Cost"
          }
        ]
      },
      {
        "title": "Escalation Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "kyros_escalation_rate_percentage",
            "legendFormat": "Escalation Rate"
          }
        ]
      },
      {
        "title": "Tasks by Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "kyros_tasks_total",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Model Usage by Role",
        "type": "barchart",
        "targets": [
          {
            "expr": "kyros_model_usage_total",
            "legendFormat": "{{role}} - {{model}}"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
```

## Custom Agent Integration

### Custom Agent Development

**Agent Interface:**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import asyncio

class CustomAgent(ABC):
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.is_available = True
    
    @abstractmethod
    async def can_handle_task(self, task: Dict[str, Any]) -> bool:
        """Check if agent can handle the task"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task and return results"""
        pass
    
    @abstractmethod
    async def get_estimates(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Return time and cost estimates for the task"""
        pass
    
    async def register_with_kyros(self, kyros_url: str, api_key: str):
        """Register agent with Kyros orchestrator"""
        registration_data = {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'status': 'available'
        }
        
        response = requests.post(
            f'{kyros_url}/v1/agents/register',
            headers={'Authorization': f'Bearer {api_key}'},
            json=registration_data
        )
        
        if response.status_code == 201:
            print(f"Agent {self.agent_id} registered successfully")
        else:
            print(f"Failed to register agent: {response.text}")
```

**Example Custom Agent:**
```python
import re
import subprocess
from typing import Dict, Any, List

class SecurityReviewAgent(CustomAgent):
    def __init__(self):
        super().__init__(
            agent_id='security_review_agent_v1',
            capabilities=[
                'security_analysis',
                'vulnerability_scanning',
                'code_review',
                'compliance_checking'
            ]
        )
        
        # Security scanning tools
        self.security_tools = {
            'bandit': 'python -m bandit -r',
            'semgrep': 'semgrep --config=auto',
            'snyk': 'snyk code test'
        }
    
    async def can_handle_task(self, task: Dict[str, Any]) -> bool:
        """Check if task involves security analysis"""
        task_type = task.get('type', '')
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        
        security_keywords = [
            'security', 'vulnerability', 'compliance', 'audit',
            'authentication', 'authorization', 'encryption',
            'owasp', 'snyk', 'bandit', 'semgrep'
        ]
        
        # Check if task type matches
        if task_type in ['security_review', 'vulnerability_scan', 'compliance_check']:
            return True
        
        # Check if keywords appear in title or description
        text = f"{title} {description}"
        return any(keyword in text for keyword in security_keywords)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security review task"""
        files_to_review = task.get('files_to_modify', [])
        results = {
            'vulnerabilities': [],
            'recommendations': [],
            'compliance_issues': [],
            'security_score': 100
        }
        
        # Run security tools on each file
        for file_path in files_to_review:
            if file_path.endswith('.py'):
                results.update(await self._analyze_python_file(file_path))
            elif file_path.endswith(('.js', '.ts')):
                results.update(await self._analyze_javascript_file(file_path))
        
        # Calculate overall security score
        total_issues = (
            len(results['vulnerabilities']) +
            len(results['compliance_issues'])
        )
        results['security_score'] = max(0, 100 - (total_issues * 5))
        
        return {
            'success': True,
            'results': results,
            'agent_used': self.agent_id,
            'execution_time': 120  # Estimated time in seconds
        }
    
    async def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file for security issues"""
        results = {
            'vulnerabilities': [],
            'compliance_issues': []
        }
        
        try:
            # Run Bandit
            bandit_result = subprocess.run(
                ['python', '-m', 'bandit', '-r', '-f', 'json', file_path],
                capture_output=True, text=True
            )
            
            if bandit_result.returncode == 0:
                bandit_output = json.loads(bandit_result.stdout)
                for issue in bandit_output.get('results', []):
                    results['vulnerabilities'].append({
                        'tool': 'bandit',
                        'severity': issue['issue_severity'],
                        'description': issue['issue_text'],
                        'line': issue['line_number'],
                        'file': file_path
                    })
            
            # Run custom security checks
            results.update(await self._run_custom_checks(file_path))
            
        except Exception as e:
            results['compliance_issues'].append({
                'tool': 'analyzer',
                'description': f'Failed to analyze file: {str(e)}',
                'severity': 'medium'
            })
        
        return results
    
    async def _run_custom_checks(self, file_path: str) -> Dict[str, Any]:
        """Run custom security checks"""
        results = {'vulnerabilities': [], 'compliance_issues': []}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for hardcoded secrets
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']'
            ]
            
            for pattern in secret_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    results['vulnerabilities'].append({
                        'tool': 'custom',
                        'severity': 'high',
                        'description': 'Potential hardcoded secret detected',
                        'line': content[:match.start()].count('\n') + 1,
                        'file': file_path
                    })
            
            # Check for SQL injection patterns
            sql_injection_patterns = [
                r'execute\([^)]*\+\s*[^)]*\)',  # String concatenation in execute
                r'cursor\.execute\([^)]*%\s*[^)]*\)',  # % formatting
                r'f["\'][^"\']*{[^}]*}[^"\']*["\']'  # f-strings with user input
            ]
            
            for pattern in sql_injection_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    results['vulnerabilities'].append({
                        'tool': 'custom',
                        'severity': 'high',
                        'description': 'Potential SQL injection vulnerability',
                        'line': content[:match.start()].count('\n') + 1,
                        'file': file_path
                    })
        
        except Exception as e:
            results['compliance_issues'].append({
                'tool': 'custom',
                'description': f'Failed to run custom checks: {str(e)}',
                'severity': 'low'
            })
        
        return results
    
    async def get_estimates(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Return time and cost estimates"""
        files_count = len(task.get('files_to_modify', []))
        complexity = task.get('complexity', 'medium')
        
        # Estimate based on file count and complexity
        base_time = 300  # 5 minutes base
        
        if complexity == 'high':
            time_multiplier = 2.0
        elif complexity == 'low':
            time_multiplier = 0.5
        else:
            time_multiplier = 1.0
        
        estimated_time = int(base_time * files_count * time_multiplier)
        estimated_cost = estimated_time * 0.02  # $0.02 per second
        
        return {
            'estimated_time_seconds': estimated_time,
            'estimated_cost_usd': estimated_cost,
            'confidence': 0.85
        }
```

## Best Practices

### Security Best Practices

**API Key Management:**
- Store API keys in environment variables or secret managers
- Rotate API keys regularly
- Use the least privilege principle
- Monitor API key usage and access patterns

**Webhook Security:**
- Always verify webhook signatures
- Use HTTPS for webhook endpoints
- Implement rate limiting for webhook handlers
- Validate and sanitize all webhook data

**Data Privacy:**
- Minimize data collection and retention
- Encrypt sensitive data at rest and in transit
- Comply with GDPR, CCPA, and other regulations
- Regularly audit data access and usage

### Performance Best Practices

**Caching Strategies:**
```python
import redis
import json

class CachedKyrosClient:
    def __init__(self, api_key, redis_url='redis://localhost:6379'):
        self.api_key = api_key
        self.redis = redis.from_url(redis_url)
        self.cache_ttl = 300  # 5 minutes
    
    def get_task(self, task_id):
        """Get task with caching"""
        cache_key = f"kyros_task:{task_id}"
        
        # Try cache first
        cached_data = self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Fetch from API
        response = requests.get(
            f'https://api.kyros.com/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        
        if response.status_code == 200:
            task_data = response.json()
            # Cache the result
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(task_data))
            return task_data['data']
        
        return None
```

**Rate Limiting:**
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, key):
        """Check if request is allowed"""
        now = time.time()
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False

# Usage
rate_limiter = RateLimiter(max_requests=100, time_window=60)

def make_api_request(key):
    if rate_limiter.is_allowed(key):
        # Make API request
        pass
    else:
        raise Exception("Rate limit exceeded")
```

### Integration Testing

**Test Strategy:**
```python
import pytest
from unittest.mock import Mock, patch

class TestKyrosIntegration:
    @pytest.fixture
    def kyros_client(self):
        with patch('kyros.KyrosClient') as mock_client:
            yield mock_client
    
    def test_task_creation(self, kyros_client):
        """Test task creation integration"""
        kyros_client.tasks.create.return_value = {
            'success': True,
            'data': {'id': 'task_123'}
        }
        
        task_data = {
            'title': 'Test task',
            'description': 'Test description',
            'type': 'implementation'
        }
        
        result = kyros_client.tasks.create(task_data)
        
        assert result['success'] is True
        assert result['data']['id'] == 'task_123'
        kyros_client.tasks.create.assert_called_once_with(task_data)
    
    def test_webhook_handling(self):
        """Test webhook event handling"""
        webhook_data = {
            'type': 'task.completed',
            'data': {
                'id': 'task_123',
                'status': 'completed'
            }
        }
        
        # Test webhook handler
        response = self.app.post(
            '/webhooks/kyros',
            json=webhook_data,
            headers={'X-Kyros-Signature': 'valid-signature'}
        )
        
        assert response.status_code == 200
        assert response.json()['status'] == 'received'
```

## Troubleshooting Integration Issues

### Common Issues

**API Authentication Failures:**
```bash
# Check API key validity
curl -X GET "$KYROS_API_URL/monitoring/health" \
  -H "Authorization: Bearer $KYROS_API_KEY"

# Common errors:
# - 401 Unauthorized: Invalid API key
# - 403 Forbidden: Insufficient permissions
# - 429 Too Many Requests: Rate limit exceeded
```

**Webhook Delivery Issues:**
```bash
# Test webhook endpoint
curl -X POST "https://your-webhook-url.com/kyros" \
  -H "Content-Type: application/json" \
  -H "X-Kyros-Signature: test-signature" \
  -d '{"type": "test", "data": {}}'

# Troubleshooting steps:
# 1. Verify webhook URL is accessible
# 2. Check SSL certificate validity
# 3. Verify webhook secret matches
# 4. Check firewall rules
# 5. Review server logs
```

**Performance Issues:**
```bash
# Test API response times
time curl -X GET "$KYROS_API_URL/monitoring/health" \
  -H "Authorization: Bearer $KYROS_API_KEY"

# Check network latency
ping api.kyros.com

# Monitor resource usage
top
htop
```

### Debug Integration

**Enable Debug Logging:**
```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('kyros_integration')

# Add debug logging to API calls
def api_call(endpoint, **kwargs):
    logger.debug(f"Making API call to {endpoint}")
    logger.debug(f"Request data: {kwargs}")
    
    response = requests.get(endpoint, **kwargs)
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response data: {response.json()}")
    
    return response
```

**Use Mock Data for Testing:**
```python
class MockKyrosClient:
    def __init__(self):
        self.tasks = []
        self.mock_responses = {
            'create_task': {'id': 'mock_task_123'},
            'get_task': {'status': 'completed'},
            'submit_agent': {'submission_id': 'mock_sub_123'}
        }
    
    def create_task(self, task_data):
        task_id = f"mock_task_{len(self.tasks) + 1}"
        self.tasks.append({
            'id': task_id,
            **task_data,
            'status': 'pending'
        })
        return {'success': True, 'data': {'id': task_id}}
    
    def get_task(self, task_id):
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if task:
            return {'success': True, 'data': task}
        return {'success': False, 'error': 'Task not found'}
```

---

## Integration Checklist

### Pre-Integration
- [ ] Obtain API credentials
- [ ] Set up development environment
- [ ] Review API documentation
- [ ] Plan integration architecture
- [ ] Set up monitoring and logging

### Development
- [ ] Implement authentication
- [ ] Create API client wrapper
- [ ] Implement webhook handlers
- [ ] Add error handling
- [ ] Write integration tests

### Testing
- [ ] Unit testing
- [ ] Integration testing
- [ ] Performance testing
- [ ] Security testing
- [ ] User acceptance testing

### Deployment
- [ ] Configure production environment
- [ ] Set up monitoring and alerting
- [ ] Deploy integration
- [ ] Monitor performance
- [ ] Document integration

### Maintenance
- [ ] Regular security updates
- [ ] Performance optimization
- [ ] Monitor usage patterns
- [ ] Update dependencies
- [ ] Regular maintenance reviews

## Next Steps

1. **Start Small**: Begin with basic API integration
2. **Add Webhooks**: Implement event-driven workflows
3. **Integrate Tools**: Connect with existing development tools
4. **Monitor Performance**: Set up comprehensive monitoring
5. **Optimize**: Continuously improve integration performance

For additional support, refer to the [API Documentation](../api/hybrid-model-api-documentation.md), [User Guide](../user-guide/hybrid-model-user-guide.md), or contact the Kyros support team.