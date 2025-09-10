#!/bin/bash
set -e

echo "Testing core..."
cd packages/core
npm test
cd ../..

echo "Testing terminal-daemon..."
cd services/terminal-daemon
npm test
cd ../..

echo "Testing console..."
cd services/console
npm test
cd ../..

echo "Testing orchestrator..."
cd kyros-praxis/services/orchestrator
pytest
cd ../../..

echo "Testing service-registry..."
cd kyros-praxis/packages/service-registry
pytest
cd ../..