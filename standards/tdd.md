# Standard: Test-Driven Development (TDD)

## 1. Red-Green-Refactor Discipline
1. **Red**: Write a failing test in `tests/` verifying the desired behavior or schema.
2. **Green**: Write minimal code to pass the test.
3. **Refactor**: Clean up duplication, enforce typing, and adhere to architecture without breaking tests.

## 2. Commit Cadence
* Commit exactly once per completed task with real verification command output.
* Tests must run deterministically in local CI before marking a task complete.
