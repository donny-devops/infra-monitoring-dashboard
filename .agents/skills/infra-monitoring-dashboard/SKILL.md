```markdown
# infra-monitoring-dashboard Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `infra-monitoring-dashboard` TypeScript codebase. It covers file naming, import/export styles, commit message conventions, and testing patterns. The repository does not use a framework, focusing on clean TypeScript organization and conventional commits for maintainability.

## Coding Conventions

### File Naming
- Use **PascalCase** for file names.
  - Example: `ServerStatus.ts`, `DashboardView.tsx`

### Import Style
- Use **relative imports** for referencing other modules within the codebase.
  - Example:
    ```typescript
    import { ServerStatus } from './ServerStatus';
    ```

### Export Style
- Use **named exports** to expose functions, classes, or constants.
  - Example:
    ```typescript
    // ServerStatus.ts
    export function getStatus() { ... }
    export const STATUS_OK = 'ok';
    ```

### Commit Message Conventions
- Use **conventional commits** with a `chore` prefix for maintenance and other changes.
  - Example:
    ```
    chore: update dependencies to latest versions
    ```

## Workflows

### Commit Changes
**Trigger:** When making any code, configuration, or dependency update.
**Command:** `/commit-changes`

1. Stage your changes:
    ```
    git add .
    ```
2. Write a commit message using the conventional format:
    ```
    git commit -m "chore: <your concise description>"
    ```
3. Push your changes:
    ```
    git push
    ```

### Run Tests
**Trigger:** Before pushing code or after making changes.
**Command:** `/run-tests`

1. Identify test files (look for files matching `*.test.*`).
2. Run your test runner (framework is unknown; typically one of `npm test`, `yarn test`, or a direct call to a test runner).
    ```
    npm test
    ```
    or
    ```
    yarn test
    ```
    or
    ```
    ts-node path/to/your/testfile.test.ts
    ```

## Testing Patterns

- **Test File Naming:** Test files use the pattern `*.test.*` (e.g., `ServerStatus.test.ts`).
- **Framework:** Not explicitly detected—use standard TypeScript/Jest/Mocha patterns.
- **Example:**
    ```typescript
    // ServerStatus.test.ts
    import { getStatus } from './ServerStatus';

    describe('getStatus', () => {
      it('returns ok when server is healthy', () => {
        expect(getStatus()).toBe('ok');
      });
    });
    ```

## Commands
| Command         | Purpose                                   |
|-----------------|-------------------------------------------|
| /commit-changes | Guide for making conventional commits     |
| /run-tests      | Steps to run tests in the codebase        |
```
