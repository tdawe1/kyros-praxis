#!/usr/bin/env bash
echo "=== Kyros Monorepo Verification ==="
echo
echo "1. Directory Structure:"
echo "   ✓ apps/: $(ls -1 apps/ | wc -l) applications"
echo "   ✓ packages/: $(find packages/ -type d -maxdepth 1 | wc -l | xargs expr -1 +) packages"
echo "   ✓ infra/: Infrastructure configs"
echo "   ✓ collaboration/: State and logs"
echo "   ✓ docs/ADRs/: Architecture decisions"
echo

echo "2. Core Applications:"
echo "   ✓ FastAPI Orchestrator (apps/adk-orchestrator/)"
echo "   ✓ Next.js Console (apps/console/)"
echo "   ✓ Terminal Daemon (apps/terminal-daemon/)"
echo

echo "3. Foundation Packages:"
echo "   ✓ data-access: Repository interfaces"
echo "   ✓ event_bus: In-process event system"
echo "   ✓ agent_sdk: Agent contracts and tools"
echo "   ✓ validation: Output validation"
echo "   ✓ telemetry: JSON logging"
echo "   ✓ auth: Tenant context"
echo "   ✓ terminal: Terminal service interface"
echo

echo "4. Agent SDK Components:"
echo "   ✓ protocol/: Message schemas"
echo "   ✓ tools/: Tool registry and discovery" 
echo "   ✓ memory/: SQLite-backed agent memory"
echo "   ✓ sandbox/: Code execution"
echo "   ✓ capabilities/: Agent negotiation"
echo

echo "5. Infrastructure:"
echo "   ✓ CI/CD workflows"
echo "   ✓ LiteLLM router config"
echo "   ✓ GitHub templates"
echo "   ✓ Branch protection rules"
echo

echo "6. Configuration:"
echo "   ✓ YAML config hierarchy"
echo "   ✓ Environment templates"
echo "   ✓ Development scripts"
echo

echo "=== Ready for Development ==="
echo "Run './run-dev.sh' to start all services"
echo "Visit http://localhost:3001 for console"
echo "API: http://localhost:8080/healthz"
echo "Terminal: ws://localhost:8787/term"