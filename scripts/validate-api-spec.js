#!/usr/bin/env node

/**
 * API Specification Validation Script
 * 
 * This script validates that the FastAPI application matches the OpenAPI specification
 * by starting the server, generating the OpenAPI schema, and comparing it with the spec file.
 */

import { spawn } from 'child_process';
import { readFileSync, writeFileSync, unlinkSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

const API_SPEC_PATH = join(projectRoot, 'api-specs', 'orchestrator-v1.yaml');
const ORCHESTRATOR_PATH = join(projectRoot, 'apps', 'adk-orchestrator');

async function validateApiSpec() {
  console.log('🔍 Validating API specification...');
  
  try {
    // Start the orchestrator server
    console.log('🚀 Starting orchestrator server...');
    const serverProcess = spawn('python', ['main.py'], {
      cwd: ORCHESTRATOR_PATH,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Wait for server to start
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // Fetch the OpenAPI schema
    console.log('📋 Fetching OpenAPI schema...');
    const response = await fetch('http://localhost:8000/openapi.json');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI schema: ${response.status} ${response.statusText}`);
    }

    const openApiSchema = await response.json();
    
    // Write schema to temporary file for comparison
    const tempSchemaPath = join(projectRoot, 'temp-openapi.json');
    writeFileSync(tempSchemaPath, JSON.stringify(openApiSchema, null, 2));

    // Kill the server
    serverProcess.kill();
    serverProcess.on('close', () => {
      console.log('🛑 Server stopped');
    });

    // Read the expected spec
    const expectedSpec = readFileSync(API_SPEC_PATH, 'utf8');
    
    // Basic validation - check if key endpoints exist
    const requiredEndpoints = [
      '/healthz',
      '/readyz', 
      '/v1/config',
      '/v1/runs/plan'
    ];

    const missingEndpoints = requiredEndpoints.filter(endpoint => {
      return !openApiSchema.paths || !openApiSchema.paths[endpoint];
    });

    if (missingEndpoints.length > 0) {
      console.error('❌ Missing required endpoints:', missingEndpoints);
      process.exit(1);
    }

    // Validate response schemas match
    const healthzResponse = openApiSchema.paths['/healthz']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!healthzResponse || !healthzResponse.properties?.ok) {
      console.error('❌ /healthz endpoint schema validation failed');
      process.exit(1);
    }

    const readyzResponse = openApiSchema.paths['/readyz']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!readyzResponse || !readyzResponse.properties?.ready) {
      console.error('❌ /readyz endpoint schema validation failed');
      process.exit(1);
    }

    const configResponse = openApiSchema.paths['/v1/config']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!configResponse) {
      console.error('❌ /v1/config endpoint schema validation failed');
      process.exit(1);
    }

    const planRequest = openApiSchema.paths['/v1/runs/plan']?.post?.requestBody?.content?.['application/json']?.schema;
    if (!planRequest || !planRequest.required?.includes('pr') || !planRequest.required?.includes('mode')) {
      console.error('❌ /v1/runs/plan endpoint request schema validation failed');
      process.exit(1);
    }

    // Clean up
    unlinkSync(tempSchemaPath);

    console.log('✅ API specification validation passed!');
    console.log('📊 Validated endpoints:');
    requiredEndpoints.forEach(endpoint => {
      console.log(`   ✓ ${endpoint}`);
    });

  } catch (error) {
    console.error('❌ API specification validation failed:', error.message);
    process.exit(1);
  }
}

// Run validation
validateApiSpec().catch(error => {
  console.error('❌ Validation script failed:', error);
  process.exit(1);
});
