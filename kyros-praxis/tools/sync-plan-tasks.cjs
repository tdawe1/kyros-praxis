#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const planPath = path.join(repoRoot, 'agents/PLAN.md');
const tasksJsonPath = path.join(repoRoot, 'collaboration/state/tasks.json');

function extractYamlBlock(md) {
  const start = md.indexOf('```yaml');
  if (start === -1) return null;
  const end = md.indexOf('```', start + 7);
  if (end === -1) return null;
  return md.slice(start + 7, end);
}

function parseTasks(yaml) {
  const lines = yaml.split(/\r?\n/);
  const tasks = [];
  let current = null;
  let mode = null;
  for (let raw of lines) {
    const line = raw.replace(/\t/g, '    ');
    if (/^\s*tasks\s*:\s*$/.test(line)) { continue; }
    const idMatch = line.match(/^\s*-\s+id:\s*(.+)\s*$/);
    if (idMatch) {
      if (current) tasks.push(current);
      current = { id: idMatch[1].trim(), title: '', owned_paths: [], commands: [], dod: [] };
      mode = null; continue;
    }
    if (!current) continue;
    const titleMatch = line.match(/^\s*title:\s*(.+)\s*$/);
    if (titleMatch) { current.title = titleMatch[1].replace(/^"|"$/g, '').trim(); continue; }
    if (/^\s*owned_paths:\s*$/.test(line)) { mode = 'owned_paths'; continue; }
    if (/^\s*commands:\s*$/.test(line)) { mode = 'commands'; continue; }
    if (/^\s*dod:\s*$/.test(line)) { mode = 'dod'; continue; }
    const li = line.match(/^\s*-\s+(.+)\s*$/);
    if (li && mode) {
      let val = li[1].trim();
      val = val.replace(/^"|"$/g, '');
      current[mode].push(val);
      continue;
    }
  }
  if (current) tasks.push(current);
  return tasks;
}

function loadJsonSafe(p) {
  if (!fs.existsSync(p)) return { meta: {}, tasks: [] };
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return { meta: {}, tasks: [] }; }
}

function main() {
  if (!fs.existsSync(planPath)) {
    console.error('PLAN.md not found at', planPath);
    process.exit(1);
  }
  const md = fs.readFileSync(planPath, 'utf8');
  const yaml = extractYamlBlock(md);
  if (!yaml) {
    console.error('No YAML block found in PLAN.md');
    process.exit(1);
  }
  const planTasks = parseTasks(yaml);
  if (!planTasks.length) {
    console.error('Parsed 0 tasks from PLAN.md YAML');
    process.exit(1);
  }
  const current = loadJsonSafe(tasksJsonPath);
  const byId = new Map((current.tasks || []).map(t => [t.id, t]));
  const merged = planTasks.map(t => {
    const prev = byId.get(t.id) || {};
    return {
      id: t.id,
      title: t.title || prev.title || t.id,
      description: prev.description || 'Synced from PLAN.md',
      dod: t.dod && t.dod.length ? t.dod : (prev.dod || []),
      owned_paths: t.owned_paths || prev.owned_paths || [],
      commands: t.commands || prev.commands || [],
      status: prev.status || 'todo',
      github_issue_number: (prev.github_issue_number === undefined ? null : prev.github_issue_number)
    };
  });
  const out = {
    meta: { source: 'agents/PLAN.md', synced_at: new Date().toISOString() },
    tasks: merged
  };
  fs.mkdirSync(path.dirname(tasksJsonPath), { recursive: true });
  fs.writeFileSync(tasksJsonPath, JSON.stringify(out, null, 2) + '\n');
  console.log(`Synced ${merged.length} tasks to ${tasksJsonPath}`);
}

if (require.main === module) main();

