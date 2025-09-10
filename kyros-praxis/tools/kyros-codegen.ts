#!/usr/bin/env node
// Minimal, idempotent placeholder CLI to avoid clashes
import { existsSync } from 'node:fs'
import { generate } from '../packages/codegen/src/index.js'

if (!existsSync('kyros-praxis/contracts')) {
  console.log('[kyros-codegen] contracts directory not found; skipping')
  process.exit(0)
}

generate()

