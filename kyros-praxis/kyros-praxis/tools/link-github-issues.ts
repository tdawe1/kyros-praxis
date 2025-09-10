#!/usr/bin/env -S node --no-warnings --loader ts-node/esm
// Minimal stub that reads collaboration/state/tasks.json and prints the payloads
// To activate creation, implement GitHub REST calls (octokit) and write back issue numbers.
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(process.cwd())
const tasksPath = path.join(root, 'collaboration/state/tasks.json')
if (!fs.existsSync(tasksPath)) {
  console.error('tasks.json not found at', tasksPath)
  process.exit(1)
}
const data = JSON.parse(fs.readFileSync(tasksPath, 'utf8'))
const tasks = data.tasks || []
for (const t of tasks) {
  if (t.github_issue_number) continue
  const title = `${t.id}: ${t.title}`
  const body = `Description:\n${t.description}\n\nDoD:\n- ${Array.isArray(t.dod) ? t.dod.join('\n- ') : ''}`
  console.log('[DRY-RUN] Would create issue:', { title, body })
}
console.log('Set GITHUB_TOKEN and implement creation to enable linking.')

