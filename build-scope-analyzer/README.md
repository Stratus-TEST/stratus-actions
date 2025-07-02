# Build Scope Analyzer

## Quick Start

```yaml
- name: Analyze Build Scope
  id: analyze
  uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "src" # Include paths containing "src"
    exclude-pattern: "test" # Exclude paths containing "test"
    comparison_ref: "main" # Optional: compare against specific ref
```

## Configuration Options

| Input             | Description                                                     | Default                   |
| ----------------- | --------------------------------------------------------------- | ------------------------- |
| `root-path`       | Root path to search for changes (defaults to GITHUB_WORKSPACE)  | `${{ github.workspace }}` |
| `include-pattern` | Pattern for paths to include (substring matching, e.g., `src`)  | `*`                       |
| `exclude-pattern` | Pattern for paths to exclude (substring matching, e.g., `test`) | `""`                      |
| `comparison_ref`  | Git ref to compare against (defaults to automatic detection)    | `""`                      |

## Overview

Build Scope Analyzer is a GitHub Action and CLI tool that analyzes changes in a git repository to determine which applications and containers need to be built, deployed, or cleaned up. It is designed for monorepos and multi-app repositories, especially those using containerized applications.

- **Smart Change Detection:** Analyzes git diffs to identify changed, deleted, and renamed files and folders
- **Deletion Tracking:** Detects deleted apps or containers for proper cleanup
- **Multi-Container Support:** Handles multiple apps and containers per repo
- **Custom Docker Build Context:** Supports custom Docker build contexts via `# @context: ...` in Dockerfiles
- **Matrix Outputs:** Generates strategy matrices for parallel builds and deployments
- **Secure & Reproducible:** Runs in a minimal, non-root Docker container for consistent results

## Inputs

| Input             | Description                                                     | Default                   |
| ----------------- | --------------------------------------------------------------- | ------------------------- |
| `root-path`       | Root path to search for changes (defaults to GITHUB_WORKSPACE)  | `${{ github.workspace }}` |
| `include-pattern` | Pattern for paths to include (substring matching, e.g., `src`)  | `*`                       |
| `exclude-pattern` | Pattern for paths to exclude (substring matching, e.g., `test`) | `""`                      |
| `comparison_ref`  | Git ref to compare against (defaults to automatic detection)    | `""`                      |

## Pattern Matching

Both `include-pattern` and `exclude-pattern` use **substring matching**:

- **Include pattern**: Only paths containing this substring will be included
- **Exclude pattern**: Paths containing this substring will be excluded
- **Exclude takes precedence**: If a path matches both include and exclude patterns, it will be excluded
- **Examples**:
  - `include-pattern: "src"` → includes paths like `src/app1`, `my-src/app2`
  - `exclude-pattern: "test"` → excludes paths like `test/app`, `src/test-app`

**Example with pattern overlap:**

For these paths:

```
src/app1/
src/app2/test/
src/app3/testfile.js
```

With these patterns:

```yaml
include-pattern: "src/app" # Match anything with 'src/app'
exclude-pattern: "test" # Exclude anything with 'test'
```

The results would be:

- ✅ `src/app1/` - Included (matches include-pattern, doesn't match exclude-pattern)
- ❌ `src/app2/test/` - Excluded (matches both patterns, but exclude wins)
- ❌ `src/app3/testfile.js` - Excluded (matches both patterns, but exclude wins)

## Git Reference Detection

The action automatically detects the appropriate git reference for comparison:

- **Push events**: Compares against `HEAD~1` (previous commit)
- **Pull Request events**: Compares against the PR base branch (`origin/{base_ref}`)
- **Manual override**: Use the `comparison_ref` input to specify a custom comparison reference
- **Workflow dispatch**: No comparison by default (useful for testing)

## Outputs

| Output           | Description                                       |
| ---------------- | ------------------------------------------------- |
| `matrix`         | JSON matrix structure with all app/container data |
| `comparison_ref` | Git ref used for comparison                       |

## Usage as a GitHub Action

```yaml
- name: Analyze Build Scope
  id: analyze
  uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "src" # Include paths containing "src"
    exclude-pattern: "test" # Exclude paths containing "test"
    comparison_ref: "main" # Optional: compare against specific ref
```

### Basic Usage Examples

**Include everything (default):**

```yaml
- uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
```

**Filter to specific directory:**

```yaml
- uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "examples/corp/container_app"
```

> **Note**: With substring matching, this will match any path containing this string, such as `my-examples/corp/container_app/subfolder`

**Include apps but exclude tests:**

```yaml
- uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "apps"
    exclude-pattern: "test"
```

> **Note**: This will include any path containing "apps" and exclude any path containing "test", so `src/apps/myapp` would be included but `src/apps/test-app` would be excluded

**Compare against specific branch:**

```yaml
- uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1
  with:
    include-pattern: "src"
    comparison_ref: "main"
```

- The action outputs a `matrix` JSON object with all changed, all, and deleted apps/containers, and the `comparison_ref` used for comparison.
- See the [example-workflow.yml](./example-workflow.yml) for a full pipeline example.

## Usage as a Docker CLI Tool

```bash
docker run --rm \
  -v "$(git rev-parse --show-toplevel):/github/workspace" \
  -e GITHUB_WORKSPACE=/github/workspace \
  ghcr.io/stratus-test/stratus-actions/build-scope-analyzer:latest \
  --root-path /github/workspace
```

- All arguments after the image name are passed to the Python program.
- The container checks for a valid git repository using git commands.
- If not run inside a git repo, a warning is shown and results may not be as expected.
- The image source is now canonical in this repository. This is the first production release (v1.0.0) after a full history reset.

## Command-line Arguments

Run with `--help` to see all options:

```bash
docker run --rm -v "$(git rev-parse --show-toplevel):/github/workspace" -e GITHUB_WORKSPACE=/github/workspace ghcr.io/stratus-test/stratus-actions/build-scope-analyzer:latest --help
```

- `--output-format github` (default) outputs for GitHub Actions
- `--output-format json` outputs plain JSON for CLI use
- `--mock-git` enables mock mode for local testing without a git repo

## Example Output Structure

The action outputs a matrix with the following structure:

```json
{
  "apps": {
    "updated": [...],
    "all": [...],
    "deleted": [...],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [...],
    "all": [...],
    "deleted": [...],
    "has_updates": true,
    "has_deletions": false
  },
  "comparison_ref": "origin/main"
}
```

- See [example-outputs.md](./example-outputs.md) for more scenarios.

## How It Works

- Detects changed, deleted, and renamed files using git diff
- Groups changes by app/container folder
- Finds Dockerfiles and app.yaml/app.yml in each folder
- Outputs a matrix for use in downstream jobs (build, deploy, cleanup)

## Development & Testing

- The action is fully tested via GitHub Actions workflows ([test-actions.yml](../.github/workflows/test-actions.yml)).
- For local testing:
  ```bash
  docker build -t build-scope-analyzer .
  docker run --rm -v "$(git rev-parse --show-toplevel):/github/workspace" -e GITHUB_WORKSPACE=/github/workspace build-scope-analyzer --root-path /github/workspace
  ```
- To run Python tests locally:
  Use standard Python unittest or pytest in the `/tests` directory.

## Troubleshooting & FAQ

- **Q: What happens if not run in a git repo?**

  - A: The action will warn and may not produce expected results. Use `--mock-git` for local testing.

- **Q: How do I debug missing or unexpected changes?**

  - A: Check the `comparison_ref` used for comparison and ensure your include/exclude patterns are correct. Use debug mode in calling workflows.

- **Q: Why are my `apps.all` and `containers.all` arrays empty?**

  - A: This usually indicates a pattern matching issue. Ensure your `include-pattern` correctly matches your directory structure using substring matching.

- **Q: How does pattern matching work?**

  - A: Both include and exclude patterns use substring matching. `include-pattern: "src"` will match any path containing "src" anywhere in the path.

- **Q: How do I use this in a fork or mirror repo?**

  - A: Ensure you have access to the correct git history and set the `comparison_ref` input if needed.

- **Q: What's the difference between `updated` and `all` arrays?**
  - A: `updated` contains only items that changed between commits, while `all` contains every discovered item regardless of changes.

## Common Use Cases

**CI/CD Optimization**: Use `updated` arrays to only build/deploy what changed:

```yaml
if: needs.analyze.outputs.apps_updated != '[]'
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.apps_updated) }}
```

**Full Rebuild/Deploy**: Use `all` arrays when you need to process everything:

```yaml
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.apps_all) }}
```

**Cleanup**: Use `deleted` arrays to clean up removed resources:

```yaml
if: needs.analyze.outputs.apps_has_deletions == 'true'
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.apps_deleted) }}
```

## Versioning & Release

- Versioning is managed via `pyproject.toml` and the release workflow. The first release is v1.0.0 after a full history reset.
- The Docker image is published to GHCR as `ghcr.io/stratus-test/stratus-actions/build-scope-analyzer:v1.0.0`.
- The next version is previewed in PRs by the `pre-merge-version.yml` workflow and finalized on merge to main.

## Migration Notes

- The action is now fully containerized and uses `main.py` as the entrypoint.
- All legacy scripts and files (e.g., `entrypoint.sh`, `docker-compose.yml`, `version.sh`, `test.sh`) are deprecated and removed.
- See this README for all up-to-date usage and development instructions.

## Contributing

- Contributions are welcome! Please open issues or pull requests in the canonical repository.
- See the [test-actions.yml](../.github/workflows/test-actions.yml) for test scenarios.
- For questions, open a discussion or contact the maintainers.
