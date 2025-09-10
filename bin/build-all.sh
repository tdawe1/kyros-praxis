#!/bin/bash
set -e

echo "Building core..."
cd packages/core
npm ci
npm run build
cd ../..

echo "Building terminal-daemon..."
cd services/terminal-daemon
npm ci
npm run build
cd ../..

echo "Building console..."
cd services/console
npm ci
npm run build
cd ../..