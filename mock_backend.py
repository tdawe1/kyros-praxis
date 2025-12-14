#!/usr/bin/env python3
"""Simple mock backend to demonstrate the frontend improvements."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Mock Backend Running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/api/auth/session")
def session():
    return {
        "user": {
            "name": "Demo User",
            "email": "demo@example.com",
            "image": None
        },
        "expires": "2025-09-14T00:00:00.000Z"
    }

@app.get("/api/v1/agents")
def get_agents():
    """Return mock agents data."""
    return {
        "agents": [
            {
                "id": "agent-1",
                "name": "Content Writer",
                "status": "active",
                "type": "AI Assistant",
                "model": "GPT-4",
                "lastActive": "2 mins ago",
                "tasksCompleted": 42,
                "successRate": "95%"
            },
            {
                "id": "agent-2",
                "name": "Code Reviewer",
                "status": "paused",
                "type": "Quality Control",
                "model": "Claude 3",
                "lastActive": "1 hour ago",
                "tasksCompleted": 128,
                "successRate": "98%"
            },
            {
                "id": "agent-3",
                "name": "Data Analyst",
                "status": "active",
                "type": "Analytics",
                "model": "GPT-4",
                "lastActive": "5 mins ago",
                "tasksCompleted": 67,
                "successRate": "92%"
            }
        ],
        "total": 3
    }

@app.get("/api/v1/inventory")
def get_inventory():
    """Return mock inventory data."""
    return {
        "items": [
            {
                "id": "SKU001",
                "name": "Widget A",
                "category": "Electronics",
                "stock": 150,
                "status": "in_stock",
                "price": 29.99,
                "reorderPoint": 50
            },
            {
                "id": "SKU002",
                "name": "Widget B",
                "category": "Hardware",
                "stock": 25,
                "status": "low_stock",
                "price": 49.99,
                "reorderPoint": 30
            },
            {
                "id": "SKU003",
                "name": "Widget C",
                "category": "Software",
                "stock": 0,
                "status": "out_of_stock",
                "price": 99.99,
                "reorderPoint": 10
            }
        ],
        "total": 3
    }

@app.get("/api/v1/tasks")
def get_tasks():
    """Return mock tasks."""
    return {
        "tasks": [
            {"id": 1, "title": "Review code", "status": "pending"},
            {"id": 2, "title": "Write documentation", "status": "completed"},
            {"id": 3, "title": "Fix bugs", "status": "in_progress"}
        ]
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MOCK BACKEND STARTING")
    print("="*60)
    print("\nThis will serve mock data to demonstrate the frontend fixes:")
    print("✅ Agents page with properly keyed React components")
    print("✅ Inventory page with fixed DataTable")
    print("✅ Clean ESLint output\n")
    print("Starting server on http://localhost:8000...")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)