---
id: rel-0.1.0
type: release
title: Release v0.1.0
status: accepted
confidence: 1.0
created: '2026-09-28T16:34:40.951551+00:00'
source: release-pipeline
evidence: []
valid_from: '2026-09-28T16:34:40.951551+00:00'
valid_to: null
supersedes: null
edges: []
---
# Release v0.1.0

## Overview
Initial public release of Kiln OS with dual pip/npx packaging, deterministic git artifact chain, 5-tier memory graph, token governor, and multi-harness adapters.

## Rehearsed Rollback Procedure
```bash
git checkout tags/v0.1.0^
python scripts/kiln doctor
```
