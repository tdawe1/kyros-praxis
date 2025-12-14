# Start Kyros Praxis Full Stack

## Quick Start Commands

### Option 1: Single Command (Background)
```bash
cd /home/thomas/kyros-praxis/apps

# Start API
cd api && /home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 > /tmp/api.log 2>&1 &
API_PID=$!
echo "API started (PID: $API_PID)"

# Start Console
cd ../console && npm run dev > /tmp/console.log 2>&1 &
CONSOLE_PID=$!
echo "Console started (PID: $CONSOLE_PID)"

# Wait for startup
sleep 8

# Test
curl -s http://localhost:8001/health && echo "✅ API ready"
curl -s http://localhost:3000/api/health && echo "✅ Console proxy ready"

echo ""
echo "🚀 Full stack running!"
echo "   Console: http://localhost:3000"
echo "   API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
```

### Option 2: Separate Terminals (Recommended for Development)

**Terminal 1 - API:**
```bash
cd /home/thomas/kyros-praxis/apps/api
/home/thomas/kyros-praxis/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Console:**
```bash
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

---

## Stop Servers

```bash
# Stop both
pkill -f "uvicorn app.main:app"
pkill -f "next dev"
```

---

## Check Status

```bash
# API
curl http://localhost:8001/health

# Console
curl http://localhost:3000

# Proxy
curl http://localhost:3000/api/health
```

---

## View Logs

```bash
# API (if running in background)
tail -f /tmp/api.log

# Console (if running in background)
tail -f /tmp/console.log
```

---

## Login

**URL**: http://localhost:3000/login  
**Email**: admin@example.com  
**Password**: AdminPass123!
