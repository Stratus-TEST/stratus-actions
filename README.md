# Stratus GitHub Actions

> **⚠️ NOTE: The canonical and maintained repository is [`stratus-test/stratus-actions`](https://github.com/stratus-test/stratus-actions). All maintenance and development are performed in the `stratus-test` organization. This repository may be mirrored or forked in other organizations (e.g., HafslundEcoVannkraft), but all issues, pull requests, and releases should be managed in `stratus-test`.**
>
> **This arrangement is temporary due to current policy constraints that prevent publishing public packages in the HafslundEcoVannkraft organization. Once these policy issues are resolved, the canonical repository location may change.**

Welcome to `stratus-actions`! This repository hosts a collection of reusable composite and Docker-based GitHub Actions to streamline workflows across repositories. The repository is public, you can easily share actions with any repository, ensuring consistency and reducing duplicated code.

## Table of Contents

- [Stratus GitHub Actions](#stratus-github-actions)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
    - [Key Benefits](#key-benefits)
  - [Repository Structure](#repository-structure)
  - [Usage](#usage)
  - [Available Actions](#available-actions)
    - [Hello World Action](#hello-world-action)
      - [Example Using Hello World Action](#example-using-hello-world-action)
    - [Hello World Docker Action](#hello-world-docker-action)
      - [Example Using Hello World Docker Action](#example-using-hello-world-docker-action)
    - [Simple Version Bump and Release Action](#simple-version-bump-and-release-action)
    - [Build Scope Analyzer Action](#build-scope-analyzer-action)
  - [Contributing](#contributing)
    - [Release Process](#release-process)
      - [1. Version Bumping (Workflow Logic)](#1-version-bumping-workflow-logic)
      - [2. Release Notes Categorization (`.github/release.yml`)](#2-release-notes-categorization-githubreleaseyml)
    - [Development Guidelines](#development-guidelines)
    - [Version Control](#version-control)
  - [License](#license)

## About

The `stratus-actions` repository is designed to simplify and standardize workflows across projects by providing a central source of reusable composite and Docker-based GitHub Actions. Each action is defined within its own folder at the repository root, making it easy to reference them directly from any repository.

### Key Benefits

- **Reusable**: Use the same action in multiple workflows and repositories, improving consistency.
- **Public Access**: As a public repository, actions here can be used in both public and private/internal repositories.
- **Containerized & Composite Actions**: Includes both composite and Docker-based actions for maximum compatibility and reproducibility.
- **Version Control**: Keep track of changes to actions across repositories, ensuring stability with tagged versions.
- **Simple and Reliable**: Actions use GitHub's native features without external dependencies.
- **Robust Test Workflows**: All actions are covered by automated test workflows for reliability.

## Repository Structure

The repository is organized with each action in its own folder at the root level:

```plaintext
stratus-actions/
├── build-scope-analyzer/
│   ├── Dockerfile
│   ├── README.md
│   ├── action.yml
│   ├── example-outputs.md
│   ├── example-workflow.yml
│   ├── main.py
│   └── pyproject.toml
├── hello-world/
│   ├── README.md
│   ├── action.yml
│   └── entrypoint.sh
├── hello-world-docker/
│   ├── README.md
│   ├── action.yml
│   ├── Dockerfile
│   └── entrypoint.sh
├── release/
│   ├── README.md
│   └── action.yml
├── .github/
│   └── workflows/
└── README.md
```

Each action has its own documentation explaining its specific usage and configuration options. See the README in each action folder for details.

## Usage

To use an action from this repository, reference it in your workflow file with the following syntax:

```yaml
uses: HafslundEcoVannkraft/stratus-actions/[action-name]@v1
```

Replace:

- `[action-name]` with the specific action folder name (e.g., `release`, `hello-world`, `hello-world-docker`, `build-scope-analyzer`)
- `@v1` with the desired version tag

**Example with Build Scope Analyzer:**

```yaml
- name: Analyze changes
  uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "src"
    exclude-pattern: "test"
```

## Available Actions

### Hello World Action

A simple example action that demonstrates the basic structure and usage of composite actions. For more information, see the [hello-world action documentation](hello-world/README.md).

#### Example Using Hello World Action

```yaml
name: Hello World Example

on:
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - name: Say Hello
        uses: HafslundEcoVannkraft/stratus-actions/hello-world@v1
```

### Hello World Docker Action

A simple Docker-based action that demonstrates how to use container actions and output handling. See the [hello-world-docker action documentation](hello-world-docker/README.md) for details.

#### Example Using Hello World Docker Action

```yaml
name: Hello World Docker Example

on:
  workflow_dispatch:

jobs:
  hello-docker:
    runs-on: ubuntu-latest
    steps:
      - name: Say Hello (Docker)
        uses: HafslundEcoVannkraft/stratus-actions/hello-world-docker@v1
        with:
          who-to-greet: "Stratus Docker"
      - name: Print Docker Action Output
        run: |
          echo "Docker action time output: ${{ steps.hello-docker.outputs.time }}"
```

### Simple Version Bump and Release Action

A lightweight action that automates version management and release creation using GitHub's native features:

**Key Features:**

- 🔄 Automatic version bumping based on PR labels or commit messages
- 📝 Native GitHub release notes (no external dependencies)
- 🏷️ Semantic versioning support
- 🎯 Zero configuration required
- 📋 Simple and reliable
- 🏷️ All tags and releases are created via the GitHub API for "Verified" status
- 🧪 Supports test tags via the `tag-prefix` input for safe testing

For detailed information about this action, see the [release action documentation](release/README.md).

### Build Scope Analyzer Action

A containerized action (Python, Docker) that analyzes git changes to determine what needs to be built, generating a strategy matrix for GitHub Actions workflows. This action helps optimize CI/CD pipelines by only building what has changed.

**Key Features:**

- 🔍 **Smart Change Detection**: Analyzes git diffs to identify modified directories
- 📊 **Strategy Matrix Generation**: Creates GitHub Actions matrices for parallel builds and deployments
- 🗑️ **Deletion Tracking**: Identifies deleted folders for cleanup operations
- 🎯 **Flexible Pattern Matching**: Supports include/exclude patterns using substring matching
- 🔄 **Multi-Event Support**: Handles push events, pull requests, and manual triggers with automatic git ref detection
- 🐳 **Containerized Execution**: Runs as a Docker container for consistent, isolated execution
- 📋 **Complete Discovery**: Provides both `updated` (changed) and `all` (discovered) arrays for maximum flexibility

**Pattern Matching:**

- Uses substring matching for both include and exclude patterns
- `include-pattern: "src"` matches any path containing "src"
- `exclude-pattern: "test"` excludes any path containing "test"

**Git Reference Detection:**

- **Push events**: Automatically compares against `HEAD~1`
- **Pull requests**: Compares against PR base branch
- **Manual override**: Use `comparison_ref` input for custom comparisons

For detailed information about this action, see the [build-scope-analyzer action documentation](build-scope-analyzer/README.md).

## Contributing

Contributions are welcome! If you'd like to add an action, improve existing ones, or report an issue, please follow these guidelines:

1. **Fork the Repository**: Create a fork and make your changes.
2. **Follow Commit Conventions**: Use conventional commit messages:
   - `feat:` or `feat()` for new features
   - `fix:` or `fix()` for bug fixes
   - Include `BREAKING` in PR title for breaking changes
3. **Open a Pull Request**: Submit a PR with a clear description of your changes.
4. **Action Documentation**: Ensure each action has a `README.md` in its folder explaining its usage.

### Release Process

This repository uses an automated release process. The first release is v1.0.0, and all previous history has been reset for clarity and maintainability.

#### 1. Version Bumping (Workflow Logic)

When a Pull Request is merged to `main`, the workflow determines the version bump based on PR labels:

- **Major** (vX.0.0): PRs with `breaking-change` or `major` label
- **Minor** (vX.Y.0): PRs with `enhancement`, `feature`, or `minor` label
- **Patch** (vX.Y.Z): All other PRs (default)

#### 2. Release Notes Categorization (`.github/release.yml`)

GitHub automatically categorizes merged PRs in release notes based on labels:

- PRs with `enhancement` or `feature` labels → 🚀 Features
- PRs with `bug` or `bugfix` labels → 🐛 Bug Fixes
- PRs with `documentation` label → 📚 Documentation
- PRs with `breaking-change` label → ⚠️ Breaking Changes
- PRs with `maintenance` or `chore` labels → 🔧 Maintenance

**Important**: The `.github/release.yml` file ONLY controls how release notes are displayed. It does NOT determine version numbers - that's handled by the workflow logic.

### Development Guidelines

- Test actions in a separate branch or fork before merging to `main`
- Use meaningful commit messages following the conventional commit format
- Each action should have README.md documentation
- Update examples in documentation to reflect any changes
- Test changes with workflows in your fork before submitting PRs

### Version Control

The repository automatically handles versioning through the release action. You don't need to manually create tags or releases. Just follow these practices:

1. Use conventional commit messages to indicate change type
2. For pre-releases, use appropriate prefixes in commit messages
3. Let the automated pipeline handle version bumping and release creation
4. Check the generated release notes and edit if necessary

## License

MIT
