# Build Scope Analyzer

## Overview

Build Scope Analyzer is a GitHub Action and CLI tool that analyzes changes in a git repository to determine which applications and containers need to be built, deployed, or cleaned up. It is designed for monorepos and multi-app repositories, especially those using containerized applications.

- **Smart Change Detection:** Analyzes git diffs to identify changed, deleted, and renamed files and folders
- **Deletion Tracking:** Detects deleted apps or containers for proper cleanup
- **Multi-Container Support:** Handles multiple apps and containers per repo
- **Custom Docker Build Context:** Supports custom Docker build contexts via `# @context: ...` in Dockerfiles
- **Matrix Outputs:** Generates strategy matrices for parallel builds and deployments
- **Secure & Reproducible:** Runs in a minimal, non-root Docker container for consistent results

## Inputs

| Input             | Description                                                    | Default                   |
| ----------------- | -------------------------------------------------------------- | ------------------------- |
| `root-path`       | Root path to search for changes (defaults to GITHUB_WORKSPACE) | `${{ github.workspace }}` |
| `include-pattern` | Glob pattern for paths to include (e.g., `apps/*`)             | `*`                       |
| `exclude-pattern` | Glob pattern for paths to exclude (e.g., `docs/*`)             | `""`                      |
| `ref`             | Git ref to compare against (defaults to automatic detection)   | `""`                      |

## Outputs

| Output   | Description                                       |
| -------- | ------------------------------------------------- |
| `matrix` | JSON matrix structure with all app/container data |
| `ref`    | Git ref used for comparison                       |

## Usage as a GitHub Action

```yaml
- name: Analyze Build Scope
  id: analyze
  uses: HafslundEcoVannkraft/stratus-actions/build-scope-analyzer@v1.0.0
  with:
    root-path: ${{ github.workspace }}
    include-pattern: "apps/*"
    exclude-pattern: "tests/*"
```

- The action outputs a `matrix` JSON object with all changed, all, and deleted apps/containers, and the `ref` used for comparison.
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
  "ref": "origin/main"
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
  - A: Check the `ref` used for comparison and ensure your include/exclude patterns are correct.
- **Q: How do I use this in a fork or mirror repo?**
  - A: Ensure you have access to the correct git history and set the `ref` input if needed.

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
