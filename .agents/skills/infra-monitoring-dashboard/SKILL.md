```markdown
# infra-monitoring-dashboard Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill covers the core development patterns and conventions used in the `infra-monitoring-dashboard` TypeScript codebase. It documents file naming, import/export styles, commit patterns, and testing conventions to ensure consistency and maintainability. While no frameworks or automated workflows were detected, this guide provides best practices and command suggestions for common development tasks.

## Coding Conventions

### File Naming
- Use **PascalCase** for all file names.
  - Example: `DashboardView.ts`, `AlertManager.test.ts`

### Import Style
- Use **relative imports** for referencing other modules.
  - Example:
    ```typescript
    import { AlertManager } from './AlertManager';
    ```

### Export Style
- Use **named exports** for all exported entities.
  - Example:
    ```typescript
    // AlertManager.ts
    export function AlertManager() { /* ... */ }
    ```

### Commit Patterns
- Follow **conventional commit** standards.
- Use the `docs` prefix for documentation changes.
- Keep commit messages concise (average ~72 characters).
  - Example:
    ```
    docs: update README with new setup instructions
    ```

## Workflows

### Documentation Updates
**Trigger:** When updating or adding documentation.
**Command:** `/update-docs`

1. Make your documentation changes.
2. Stage and commit using the `docs:` prefix.
    ```bash
    git add .
    git commit -m "docs: update usage section in README"
    ```
3. Push your changes and open a pull request if needed.

### Adding or Modifying Code
**Trigger:** When implementing new features or fixing bugs.
**Command:** `/update-code`

1. Create or update TypeScript files using PascalCase naming.
2. Use relative imports and named exports as per conventions.
3. Write or update corresponding test files (`*.test.*`).
4. Commit changes with a descriptive message.
    ```bash
    git add .
    git commit -m "feat: add AlertManager component"
    ```
5. Push your branch and open a pull request.

## Testing Patterns

- Test files follow the `*.test.*` pattern (e.g., `DashboardView.test.ts`).
- The specific testing framework is not specified; ensure tests are colocated with source files and named accordingly.
- Example test file:
    ```typescript
    // AlertManager.test.ts
    import { AlertManager } from './AlertManager';

    describe('AlertManager', () => {
      it('should initialize correctly', () => {
        // Test implementation
      });
    });
    ```

## Commands
| Command         | Purpose                                        |
|-----------------|------------------------------------------------|
| /update-docs    | Update or add documentation                    |
| /update-code    | Add or modify code following conventions       |
```
