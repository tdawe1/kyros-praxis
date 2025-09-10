# Version Control Strategy for Kyros Praxis

This document outlines the version control strategy for the Kyros Praxis project, including branching model, commit conventions, pull request workflows, code reviews, and merge strategies. This strategy ensures consistent, high-quality contributions and enforces best practices for collaboration.

## Branching Model

We use a trunk-based development model with GitFlow elements for releases, adapted for a monorepo with multiple services (backend/frontend). 

- **Main Branch**: The default branch. All changes merge here. Protected to require CI passing and 1 approving review.
- **Feature Branches**: `feat/<task-id>-slug` (e.g., feat/TDS-1-feature-name). Branch from main for new features. Prefix with task ID for traceability.
- **Bugfix Branches**: `fix/<task-id>-slug` (e.g., fix/TDS-2-bug-fix). For bug fixes.
- **Hotfix Branches**: `hotfix/<task-id>-slug`. For urgent production fixes. Branch from main, merge back to main.
- **Release Branches**: `release/v<major>.<minor>` (e.g., release/v1.2). For preparing releases. Merge to main after testing.
- **Long-lived Branches**: Avoid. Keep branches short-lived to promote frequent integration.

Rules:
- Branch from main for all features/bugfixes.
- Name branches with task ID (TDS-XXX) for tracking.
- Delete branches after merging to keep the repo clean.

## Commit Conventions

Use Conventional Commits for all commits to enable automated changelog generation and semantic versioning.

Format: `<type>[optional scope]: <description>`

Types:
- `feat`: New feature (e.g., feat(TDS-1): add PR template).
- `fix`: Bug fix.
- `docs`: Documentation changes.
- `style`: Formatting, missing whitespace.
- `refactor`: Code refactor without behavior change.
- `test`: Adding missing tests or correcting broken tests.
- `chore`: Build process or auxiliary tool changes.
- `ci`: CI configuration changes.
- `perf`: Performance improvements.
- `build`: Build system or external dependencies changes.
- `revert`: Revert a previous commit.

Scope: Optional, e.g., (console) or (orchestrator).

Description: Brief summary of the change. Reference task ID if applicable (e.g., (TDS-123)).

Examples:
- feat(console): add TanStack Query provider (TDS-1)
- fix(orchestrator): resolve ETag issue in task creation (TDS-2)

Enforcement: Pre-commit hooks and CI will lint commit messages. Use commitlint in CI for validation.

## Pull Request Workflows

All changes must be made via pull requests (PRs) to main. PRs must pass CI and have at least 1 approving review.

### Creating a PR
- Branch from main using the appropriate prefix (feat, fix, etc.).
- Use the PR template (.github/pull_request_template.md) for description, related issues, testing, and changes.
- Title: Follow conventional commit format (e.g., "feat(console): implement new page (TDS-1)").
- Labels: Auto-applied based on template (type: feat, status: review-needed).
- Assign reviewers and link to task/issue.

### PR Requirements
- Passes all CI checks (build, lint, tests, security scan).
- At least 1 approving review.
- No conflicts.
- Updates documentation if necessary.
- For UI changes, include screenshots.
- Follow checklist in template (conventional commit, tests, docs, no breaking changes).

### PR Review Process
- Assignee: Reviewers assigned via template.
- Reviewers check for:
  - Code quality and best practices.
  - Tests cover the change.
  - Documentation updated.
  - No breaking changes (or documented).
- Approve or request changes with specific feedback.
- Once approved and CI passes, merge via squash or rebase (prefer squash to keep history clean).

## Code Reviews

Code reviews are mandatory for all PRs to ensure quality and knowledge sharing.

### Reviewer Responsibilities
- Verify implementation matches requirements.
- Check for bugs, edge cases, security issues.
- Ensure tests are sufficient and pass.
- Confirm adherence to coding standards (linting passes).
- Provide constructive feedback within 24 hours.
- Approve if all good; request changes if needed.

### Author Responsibilities
- Address all feedback promptly.
- Update PR and notify reviewers.
- Re-run CI after changes.
- Thank reviewers upon completion.

Tools: Use GitHub PR comments for feedback. For complex changes, suggest pairing or additional reviewers.

## Merge Strategies

- **Squash and Merge**: Preferred. Combines commits into one with a conventional commit message.
- **Rebase and Merge**: For clean history if the PR has few commits.
- **Merge Commit**: Avoid unless for release branches.

Post-merge:
- Delete source branch.
- Update task/issue with PR link.
- Monitor CI for any post-merge issues.

## Enforcement and Tools

- **Pre-Commit Hooks**: Local hooks for linting, formatting, and commit message validation.
- **CI/CD**: GitHub Actions (kyros-ci.yml) runs on PRs/pushes to main: linting (ruff, eslint), tests (pytest, npm test), security scan (Trivy).
- **Branch Protection**: Main branch requires CI pass and 1 approval.
- **Templates**: PR and issue templates enforce structure.
- **Commitlint**: Validates conventional commits in CI.

This strategy promotes efficient collaboration and high code quality. For questions, reference this doc or ask in #dev channel.

Last updated: [Date]