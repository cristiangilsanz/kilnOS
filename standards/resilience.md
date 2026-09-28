# Standard: Resilience & Degradation

## 1. Fail-Closed vs Fail-Open
* **Security & Gates**: Fail closed. If secret scanner or branch check fails or errors, block the action immediately.
* **Helper Hooks**: Fail open. If cache warmup or formatting fails, emit a warning and proceed.

## 2. Rebuildability
* Derived caches (SQLite indexes, ASTs) must be disposable.
* Rebuilding from source files must produce identical query results.
