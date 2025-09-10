# Migration Report

Date: 2025-09-10T03:30:30+0100

Archives: archive/20250910-032855/services_deprecated.tgz, archive/20250910-032855/packages_deprecated.tgz, archive/20250910-032855/kyros_praxis_dotgit.tgz

## Diff Summary (source files)
- orchestrator: only-in-deprecated=18, differing=11
- console: only-in-deprecated=8, differing=11
- service-registry: only-in-deprecated=9, differing=2

## High‑signal differences
- orchestrator: auth.py, database.py, main.py, models.py, requirements.txt
- console: app/layout.tsx, app/page.tsx, contracts/api-client.yaml, src/lib/*, package.json
- service-registry: main.py, Dockerfile

## Artifacts
- Reports: tools/migration/reports/*.src2.diff-q.txt
- Patches: tools/migration/patches/*.src2.patch
