# TODO Burn-Down Tracking

## Overview
This document tracks all TODO items in the Kyros Praxis codebase. Items are categorized by type and priority.

## Categories

### 1. Unit Tests (P0 - CRITICAL)
- [ ] `/kyros-praxis/services/orchestrator/tests/unit/test_generated.py` - Replace placeholder with real tests
  - Health-check endpoint test (200 OK)
  - Sample CRUD route test using async HTTPX & test DB session
  - Failure path test (422 validation)

### 2. Tokenizer Integration (P1 - HIGH)
- [ ] `/kyros-praxis/zen-mcp-server/providers/gemini.py:352` - Use actual Gemini tokenizer when available in SDK
- [ ] `/kyros-praxis/zen-mcp-server/utils/model_context.py:163` - Integrate model-specific tokenizers

### 3. Workflow/CI Items (P2 - MEDIUM)
- [ ] `.claude/workflows/submit-pr-gate.md` - search_files for TODO/console.log and list
- [ ] `.codex/rules/workflows/submit-pr-gate.md` - search_files for TODO/console.log and list
- [ ] `.kilocode/workflows/submit-pr-gate.md` - search_files for TODO/console.log and list

### 4. NextAuth/Console TODOs (P1 - HIGH)
- [ ] `/kyros-praxis/services/console/.next/server/app/api/auth/[...nextauth]/route.js` - Multiple TODO items in auth flow
  - Authorization server token endpoint
  - Authorization server userinfo endpoint

### 5. External Dependencies (IGNORED - Not Project Code)
- Virtual environment pip packages (~50+ items in .venv directories)
- Node modules dependencies

## Progress Tracking

| Category | Total | Completed | Remaining | Percentage |
|----------|-------|-----------|-----------|------------|
| Unit Tests | 1 | 0 | 1 | 0% |
| Tokenizer | 2 | 0 | 2 | 0% |
| Workflows | 3 | 0 | 3 | 0% |
| Auth/Console | 2 | 0 | 2 | 0% |
| **TOTAL** | **8** | **0** | **8** | **0%** |

## Full Repository TODO Scan (2025-09-13)

Total TODOs found in repository: **10 items**

### Categorized List:
1. **Unit Tests** (1 item):
   - `scripts/pr_gate.py:204` - Replace with real tests

2. **Workflows** (2 items):
   - `kyros-praxis/.claude/workflows/submit-pr-gate.md:2` - search_files for TODO/console.log
   - `kyros-praxis/.codex/rules/workflows/submit-pr-gate.md:2` - search_files for TODO/console.log

3. **Documentation/Meta** (5 items):
   - `AUDIT_REPORT.md` - Multiple references to TODO debt metrics
   - `TODO: add integrator role.txt:1` - Add integrator role
   - `agents/README.md:272` - SUMMARY.md generation note
   - `kyros-praxis/codex-old-setup-revise.toml:1` - Revise codex-cli config

4. **Tokenizer** (0 items explicitly in grep, but known from code review):
   - Known from code: `zen-mcp-server/providers/gemini.py:352`
   - Known from code: `zen-mcp-server/utils/model_context.py:163`

## Priority Order
1. Unit Tests - Critical for code quality
2. Auth/Console - Security implications
3. Tokenizer - Performance optimization
4. Workflows - CI/CD improvements

Last Updated: 2025-09-13
