# Release & Rollout Plan: {{version}}

## 1. Scope & Artifact Verification
- Verified Work Tasks: {{work_tasks}}
- Clean CI Status: Required

## 2. Rehearsed Rollback Procedure
```bash
git checkout tags/{{previous_stable_version}}
python scripts/kiln doctor
```

## 3. Human Gate Signoff
- Production Gate Checkpoint: Pending Human Approval
- Agent stops at prod gate.
