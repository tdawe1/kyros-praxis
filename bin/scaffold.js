#!/usr/bin/env node

const { Command } = require('commander');
const yaml = require('js-yaml');
const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');

const program = new Command();
const STATE_FILE = path.join(__dirname, '../.scaffold-state.json');
const MANIFEST_FILE = path.join(__dirname, '../manifest.yaml');

// Load state (idempotency checkpoint)
function loadState() {
  if (fs.existsSync(STATE_FILE)) {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  }
  return { scaffolded: [] };
}

// Save state
function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

// Load manifest
function loadManifest() {
  if (!fs.existsSync(MANIFEST_FILE)) {
    throw new Error('Manifest not found. Run init first.');
  }
  try {
    const content = fs.readFileSync(MANIFEST_FILE, 'utf8');
    const manifest = yaml.load(content);
    if (!manifest || !manifest.monorepo || !manifest.monorepo.packages) {
      throw new Error('Invalid manifest structure: missing monorepo.packages');
    }
    console.log('Manifest loaded successfully. Packages count:', manifest.monorepo.packages.length);
    return manifest;
  } catch (error) {
    console.error(`Failed to parse manifest: ${error.message}`);
    console.error('Raw content first 200 chars:', fs.readFileSync(MANIFEST_FILE, 'utf8').substring(0, 200));
    throw error;
  }
}

// Check if item is scaffolded
function isScaffolded(state, item) {
  return state.scaffolded.includes(item);
}

// Mark as scaffolded
function markScaffolded(state, item) {
  if (!isScaffolded(state, item)) {
    state.scaffolded.push(item);
    saveState(state);
  }
}

// Create directory if not exists (idempotent)
function createDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirpSync(dir);
    console.log(`Created directory: ${dir}`);
  } else {
    console.log(`Directory exists: ${dir}`);
  }
}

// Init package manager based on language
function initPackageManager(dir, language) {
  const item = `init-pm:${dir}`;
  const state = loadState();
  if (isScaffolded(state, item)) {
    console.log(`Package manager already initialized: ${dir}`);
    return;
  }

  process.chdir(dir);
  try {
    if (language === 'typescript' || language === 'javascript') {
      execSync('npm init -y', { stdio: 'inherit' });
      execSync('npm install', { stdio: 'inherit' });
    } else if (language === 'python') {
      execSync('pip install -r requirements.txt', { stdio: 'inherit' });
    }
    console.log(`Initialized package manager for ${language} in ${dir}`);
    markScaffolded(state, item);
  } catch (error) {
    console.error(`Failed to init package manager: ${error.message}`);
  } finally {
    process.chdir(path.join(__dirname, '..'));
  }
}

// Generate boilerplate file
function generateBoilerplate(dir, type, language) {
  const mainFile = language === 'python' ? 'main.py' : 'index.js';
  const content = `// ${type} service boilerplate\ndeclare const KYROS_CONFIG: any;\n\nconsole.log('Kyros ${type} starting...');\n\n// DI container, contracts, etc. to be injected\n`;
  fs.writeFileSync(path.join(dir, mainFile), content);
  console.log(`Generated ${mainFile} in ${dir}`);
}

// Scaffold single package/service
function scaffoldItem(manifest, itemName, state) {
  console.log(`ScaffoldItem: looking for ${itemName}, manifest.packages?`, !!manifest.packages);
  const item = (manifest.packages || (manifest.monorepo && manifest.monorepo.packages) || []).find(p => p.name === itemName);
  if (!item) {
    console.error(`Item not found: ${itemName}`);
    return;
  }

  const fullPath = path.join(process.cwd(), item.path);
  const scaffoldKey = `scaffold:${itemName}`;

  if (isScaffolded(state, scaffoldKey)) {
    console.log(`Already scaffolded: ${itemName}`);
    return;
  }

  createDir(fullPath);
  initPackageManager(fullPath, item.language);
  generateBoilerplate(fullPath, itemName, item.language);

  // Generate contracts if defined
  if (item.contracts) {
    const contractsDir = path.join(fullPath, 'contracts');
    createDir(contractsDir);
    item.contracts.forEach(contract => {
      let schemaContent = contract.schema;
      let fileExt = 'json';
      if (contract.type === 'protobuf') {
        fileExt = 'proto';
        schemaContent = schemaContent || '// Protobuf schema to be defined';
      } else if (contract.type === 'openapi') {
        fileExt = 'yaml';
        schemaContent = schemaContent || '# OpenAPI schema to be defined';
      } else if (contract.type === 'websocket' || contract.type === 'http' || contract.type === 'jwt') {
        fileExt = 'json';
        schemaContent = schemaContent || '{}';
      }
      const fileName = `${contract.name}.${fileExt}`;
      fs.writeFileSync(path.join(contractsDir, fileName), schemaContent);
      console.log(`Generated contract ${fileName} in ${contractsDir}`);
    });
  }

  markScaffolded(state, scaffoldKey);
  console.log(`Scaffolded: ${itemName} at ${item.path}`);
}

// Main commands
program
  .name('kyros-scaffold')
  .description('Idempotent scaffolding tool for Kyros monorepo')
  .version('1.0.0');

program
  .command('init')
  .description('Initialize scaffolding state')
  .action(() => {
    const state = loadState();
    saveState(state); // Ensure file exists
    console.log('Scaffolding state initialized.');
  });

program
  .command('generate')
  .description('Generate all services/packages from manifest')
  .action(() => {
    const manifest = loadManifest();
    const state = loadState();
    console.log('Generate action: manifest.monorepo.packages?', !!manifest.monorepo && !!manifest.monorepo.packages);
    console.log('Generate action: manifest.packages?', !!manifest.packages);
    if (manifest.packages) {
      manifest.packages.forEach(pkg => {
        scaffoldItem(manifest, pkg.name, state);
      });
    } else if (manifest.monorepo && manifest.monorepo.packages) {
      manifest.monorepo.packages.forEach(pkg => {
        scaffoldItem(manifest, pkg.name, state);
      });
    } else {
      console.error('No packages found in manifest');
    }
    console.log('Generation complete.');
  });

program
  .command('validate')
  .description('Validate manifest and scaffolded state')
  .action(() => {
    try {
      const manifest = loadManifest();
      const state = loadState();
      const scaffoldedItems = state.scaffolded.filter(s => s.startsWith('scaffold:')).map(s => s.split(':')[1]);
      const missing = manifest.packages.filter(p => !scaffoldedItems.includes(p.name));
      if (missing.length > 0) {
        console.log(`Missing scaffolded items: ${missing.map(m => m.name).join(', ')}`);
      } else {
        console.log('All items validated.');
      }
    } catch (error) {
      console.error(`Validation failed: ${error.message}`);
    }
  });

program.parse();