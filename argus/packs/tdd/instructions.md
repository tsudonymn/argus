# Test-Driven Development (TDD)

## Core Rule
Never write or modify production code before there exists at least one failing test for the targeted behaviour. (TDD Guard contract — see: news.lavx.hu/article/tdd-guard)

## The Workflow
RED → GREEN → Commit → REFACTOR → Commit

The Test-Driven Development (TDD) community generally favors
RED → GREEN → Commit → REFACTOR → Commit.

1. **RED**: Write a failing test.
2. **Green**: Write the bare minimum code to pass.
3. **Commit 1**: Save a known working state (`feat` or `test: make X pass`).
4. **Refactor**: Clean up duplication, improve naming, or reorganize architecture
   without changing behavior.
5. **Commit 2**: Save your design cleanup (`refactor: clean up X`).

## Coverage Threshold
- Minimum 80% unit test coverage for all changed code (NIST-aligned standard)
- 100% coverage required for critical paths (payment processing, authentication, data integrity)
- Integration tests and E2E tests do NOT count toward the 80% unit coverage threshold

## Test Structure (Given-When-Then)
```
def test_<behaviour>_when_<condition>():
    # Given
    <setup state>
    # When
    <perform action>
    # Then
    assert <expected outcome>
```

## Red Flags — Stop and Correct
- Implementation file modified before any test file exists for that behaviour
- Tests written after implementation to confirm existing code (not to specify behaviour)
- "I'll add tests later"
- Test file created after the implementation already passes
- Batching multiple RED phases before going GREEN
- Tests that don't assert anything meaningful (trivial pass-through tests)
