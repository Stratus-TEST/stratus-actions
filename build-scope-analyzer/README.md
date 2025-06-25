# Build Scope Analyzer

## Overview

Build Scope Analyzer is a GitHub Action and CLI tool that analyzes changes in a git repository to determine which applications and containers need to be built, deployed, or cleaned up. It is designed for monorepos and multi-app repositories, especially those using containerized applications.

- **Smart Change Detection:** Analyzes git diffs to identify changed files and folders
- **Deletion Tracking:** Detects deleted apps or containers for proper cleanup
- **Multi-Container Support:** Handles multiple apps and containers per repo
- **Custom Docker Build Context:** Supports custom Docker build contexts via `# @context: ...` in Dockerfiles
- **Matrix Outputs:** Generates strategy matrices for parallel builds and deployments
- **Secure & Reproducible:** Runs in a minimal, non-root Docker container for consistent results

## Usage as a GitHub Action

```yaml
- name: Analyze Build Scope
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/stratus-gh-actions/build-scope-analyzer@vX.Y.Z
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
  ghcr.io/hafslundecoVannkraft/stratus-gh-actions/build-scope-analyzer:latest \
  --root-path /github/workspace
```

- All arguments after the image name are passed to the Python program.
- The container checks for a valid git repository using git commands.
- If not run inside a git repo, a warning is shown and results may not be as expected.

## Command-line Arguments

Run with `--help` to see all options:

```bash
docker run --rm -v "$(git rev-parse --show-toplevel):/github/workspace" -e GITHUB_WORKSPACE=/github/workspace build-scope-analyzer --help
```

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

## Development & Testing

- The action is fully tested via GitHub Actions workflows.
- For local testing:
  ```bash
  docker build -t build-scope-analyzer .
  docker run --rm -v "$(git rev-parse --show-toplevel):/github/workspace" -e GITHUB_WORKSPACE=/github/workspace build-scope-analyzer --root-path /github/workspace
  ```
- To run Python tests locally:
  Use standard Python unittest or pytest in the `/tests` directory.

## Versioning & Release

- Versioning is managed via `pyproject.toml` and the release workflow.
- Releases are created via the release workflow, which tags the repo and Docker image with the semantic version.
- The Docker image is published to GHCR as `ghcr.io/hafslundecoVannkraft/stratus-gh-actions/build-scope-analyzer:<version>`.
- The next version is previewed in PRs by the `pre-merge-version.yml` workflow and finalized on merge to main.

## Migration Notes

- The action is now fully containerized and uses `main.py` as the entrypoint.
- All legacy scripts and files (e.g., `entrypoint.sh`, `docker-compose.yml`, `version.sh`, `test.sh`) are deprecated and removed.
- See this README for all up-to-date usage and development instructions.

