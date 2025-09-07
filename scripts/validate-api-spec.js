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
import YAML from 'yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

const API_SPEC_PATH = join(projectRoot, 'api-specs', 'orchestrator-v1.yaml');
const ORCHESTRATOR_PATH = join(projectRoot, 'apps', 'adk-orchestrator');

async function validateApiSpec() {
  console.log('🔍 Validating API specification...');
  
  let serverProcess = null;
  const tempSchemaPath = join(projectRoot, 'temp-openapi.json');
  
  try {
    // Start the orchestrator server
    console.log('🚀 Starting orchestrator server...');
    serverProcess = spawn('python', ['main.py'], {
      cwd: ORCHESTRATOR_PATH,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Wait for server to be ready with proper readiness check
    console.log('⏳ Waiting for server readiness...');
    let ready = false;
    for (let i = 0; i < 30; i++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 2000);
        
        const response = await fetch('http://localhost:8000/readyz', {
          signal: controller.signal
        });
        clearTimeout(timeout);
        
        if (response.ok) {
          ready = true;
          break;
        }
      } catch (error) {
        // Server not ready yet, continue waiting
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    if (!ready) {
      throw new Error('Server failed to become ready within 30 seconds');
    }

    // Fetch the OpenAPI schema with timeout
    console.log('📋 Fetching OpenAPI schema...');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch('http://localhost:8000/openapi.json', {
      signal: controller.signal
    });
    clearTimeout(timeout);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch OpenAPI schema: ${response.status} ${response.statusText}`);
    }

    const openApiSchema = await response.json();
    
    // Write schema to temporary file for comparison
    writeFileSync(tempSchemaPath, JSON.stringify(openApiSchema, null, 2));

    // Read the expected spec
    const specYaml = readFileSync(API_SPEC_PATH, 'utf8');
    const expected = YAML.parse(specYaml);
    const specPaths = Object.keys(expected.paths || {});
    const missingFromRuntime = specPaths.filter((p) => !openApiSchema.paths?.[p]);
    if (missingFromRuntime.length) {
      console.error('❌ Runtime schema missing paths from spec:', missingFromRuntime);
      throw new Error(`Missing endpoints: ${missingFromRuntime.join(', ')}`);
    }

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
      throw new Error(`Missing required endpoints: ${missingEndpoints.join(', ')}`);
    }

    // Validate response schemas match
    const healthzResponse = openApiSchema.paths['/healthz']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!healthzResponse || !healthzResponse.properties?.ok) {
      console.error('❌ /healthz endpoint schema validation failed');
      throw new Error('/healthz endpoint schema validation failed');
    }

    const readyzResponse = openApiSchema.paths['/readyz']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!readyzResponse || !readyzResponse.properties?.ready) {
      console.error('❌ /readyz endpoint schema validation failed');
      throw new Error('/readyz endpoint schema validation failed');
    }

    const configResponse = openApiSchema.paths['/v1/config']?.get?.responses?.['200']?.content?.['application/json']?.schema;
    if (!configResponse) {
      console.error('❌ /v1/config endpoint schema validation failed');
      throw new Error('/v1/config endpoint schema validation failed');
    }

    const planRequest = openApiSchema.paths['/v1/runs/plan']?.post?.requestBody?.content?.['application/json']?.schema;
    if (!planRequest || !planRequest.required?.includes('pr') || !planRequest.required?.includes('mode')) {
      console.error('❌ /v1/runs/plan endpoint request schema validation failed');
      throw new Error('/v1/runs/plan endpoint request schema validation failed');
    }

    console.log('✅ API specification validation passed!');
    console.log('📊 Validated endpoints:');
    requiredEndpoints.forEach(endpoint => {
      console.log(`   ✓ ${endpoint}`);
    });

  } catch (error) {
    console.error('❌ API specification validation failed:', error.message);
    throw error;
  } finally {
    // Clean up resources
    if (serverProcess) {
      console.log('🛑 Stopping server...');
      serverProcess.kill('SIGTERM');
      
      // Wait for process to exit gracefully
      await new Promise((resolve) => {
        serverProcess.on('exit', resolve);
        setTimeout(() => {
          serverProcess.kill('SIGKILL');
          resolve();
        }, 5000);
      });
    }
    
    // Clean up temp file
    try {
      if (tempSchemaPath) {
        unlinkSync(tempSchemaPath);
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  }
}

// Run validation
validateApiSpec().catch(error => {
  console.error('❌ Validation script failed:', error);
  process.exit(1);
});