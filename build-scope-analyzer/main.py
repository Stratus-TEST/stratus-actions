#!/usr/bin/env python3
"""
Build Scope Analyzer V4 - Simplified file-discovery approach

This script uses file discovery to find all apps and containers in a repository,
then applies change detection and pattern filtering.
"""

import os
import sys
import json
import subprocess
import argparse
import fnmatch
import yaml
import logging
import re
import getpass
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any


class BuildScopeAnalyzer:
    """Analyzes git changes and generates strategy matrix output using file discovery"""

    def __init__(self, root_path: str, include_pattern: str = '', exclude_pattern: str = '', mock_git: bool = False):
        self.root_path = Path(root_path).resolve()
        self.include_pattern = self._normalize_pattern(include_pattern)
        self.exclude_pattern = exclude_pattern
        self.changed_files: Set[Path] = set()
        self.deleted_files: Set[Path] = set()
        self.renamed_files: Dict[Path, Path] = {}
        self.mock_git = mock_git

    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize include patterns - treat '/', '.', './' as empty (whole repo)"""
        if pattern in ['/', '.', './']:
            return ''
        return pattern

    def _normalize_azure_name(self, name: str) -> str:
        """Normalize a name to be Azure resource compatible"""
        name = name.lower()
        name = re.sub(r'[^a-z0-9-]', '-', name)
        name = re.sub(r'-+', '-', name)
        name = name.strip('-')
        return name

    def run_git_command(self, cmd: List[str]) -> str:
        """Execute a git command and return output"""
        if self.mock_git:
            cmd_str = " ".join(cmd)
            if "rev-parse" in cmd_str:
                return "mock-sha-12345"
            if "diff --name-status" in cmd_str:
                return "M\tapp.yaml\nA\tsrc/app1/Dockerfile\nD\tsrc/app2/app.yml"
            return ""

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Git command failed: {' '.join(cmd)}")
            logging.error(f"Error: {e.stderr}")
            sys.exit(1)

    def get_event_type(self) -> str:
        """Get GitHub event type from environment"""
        return os.environ.get('GITHUB_EVENT_NAME', 'push')

    def get_comparison_ref(self) -> Tuple[str, Optional[str]]:
        """Determine the reference to compare against"""
        event_type = self.get_event_type()

        if event_type == 'pull_request':
            base_ref = os.environ.get('GITHUB_BASE_REF', 'main')
            ref_name = f"origin/{base_ref}"
        elif event_type == 'workflow_dispatch':
            return "", None
        else:
            ref_name = "HEAD~1"

        try:
            commit_sha = self.run_git_command(['git', 'rev-parse', ref_name])
            return ref_name, commit_sha
        except:
            return ref_name, None

    def get_changed_files(self) -> Tuple[Set[Path], Set[Path], Dict[Path, Path]]:
        """Get list of changed, deleted, and renamed files from git diff"""
        ref_name, commit_sha = self.get_comparison_ref()

        if not ref_name:
            return set(), set(), {}

        diff_output = self.run_git_command(['git', 'diff', '--name-status', ref_name])

        changed = set()
        deleted = set()
        renamed = {}

        for line in diff_output.splitlines():
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 2:
                continue

            status = parts[0]
            if status == 'D':
                deleted.add(Path(parts[1]))
            elif status == 'R' and len(parts) >= 3:
                old_path = Path(parts[1])
                new_path = Path(parts[2])
                renamed[old_path] = new_path
                changed.add(new_path)
            elif status in ['A', 'M']:
                changed.add(Path(parts[1]))

        return changed, deleted, renamed

    def discover_files(self) -> Dict[str, List[Path]]:
        """Discover all relevant files in the repository"""
        discovered = {
            'app_configs': [],  # app.yaml, app.yml
            'dockerfiles': []   # Dockerfile, Dockerfile.*
        }

        # Use pathlib to find files recursively
        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(self.root_path)
            filename = file_path.name

            # Find app configs
            if filename in ['app.yaml', 'app.yml']:
                discovered['app_configs'].append(relative_path)

            # Find dockerfiles
            elif filename == 'Dockerfile' or filename.startswith('Dockerfile.'):
                discovered['dockerfiles'].append(relative_path)

        logging.info(f"Discovered {len(discovered['app_configs'])} app configs, {len(discovered['dockerfiles'])} dockerfiles")
        return discovered

    def should_include_path(self, path: Path) -> bool:
        """Check if path should be included based on patterns"""
        path_str = str(path)

        # Check include pattern
        if self.include_pattern:
            if not fnmatch.fnmatch(path_str, self.include_pattern):
                return False

        # Check exclude pattern
        if self.exclude_pattern:
            if fnmatch.fnmatch(path_str, self.exclude_pattern):
                return False

        return True

    def extract_app_name_from_yaml(self, yaml_path: Path) -> Optional[str]:
        """Extract the 'name' property from app.yaml/app.yml"""
        try:
            with open(self.root_path / yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'name' in data:
                    return str(data['name'])
        except Exception as e:
            logging.debug(f"Could not read app name from {yaml_path}: {e}")
        return None

    def get_dockerfile_context(self, dockerfile_path: Path) -> str:
        """Extract custom context from Dockerfile or use default"""
        try:
            with open(self.root_path / dockerfile_path, 'r') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if line.strip().startswith('# @context:'):
                        return line.strip().split(':', 1)[1].strip()
        except Exception:
            pass
        return str(dockerfile_path.parent)

    def build_unified_inventory(self, discovered: Dict[str, List[Path]]) -> Dict[str, Dict]:
        """Build unified inventory of all apps and containers"""
        inventory = {}

        # Group files by folder
        folders = {}

        # Process app configs
        for app_config_path in discovered['app_configs']:
            folder = app_config_path.parent
            if folder not in folders:
                folders[folder] = {'app_config': None, 'dockerfiles': []}
            folders[folder]['app_config'] = app_config_path

        # Process dockerfiles
        for dockerfile_path in discovered['dockerfiles']:
            folder = dockerfile_path.parent
            if folder not in folders:
                folders[folder] = {'app_config': None, 'dockerfiles': []}
            folders[folder]['dockerfiles'].append(dockerfile_path)

        # Build inventory for each folder
        for folder, files in folders.items():
            # Skip if no relevant files
            if not files['app_config'] and not files['dockerfiles']:
                continue

            # Apply include/exclude filtering
            if not self.should_include_path(folder):
                continue

            # Determine app name
            app_name = None
            if files['app_config']:
                app_name = self.extract_app_name_from_yaml(files['app_config'])

            # Fallback to folder name (normalized for root)
            if not app_name:
                if folder == Path('.'):
                    app_name = self._normalize_azure_name(self.root_path.name)
                else:
                    app_name = self._normalize_azure_name(folder.name)

            # Create folder entry
            folder_key = str(folder)
            inventory[folder_key] = {
                'path': str(folder),
                'app_name': app_name,
                'app_config': str(files['app_config']) if files['app_config'] else None,
                'dockerfiles': []
            }

            # Add dockerfile info
            for dockerfile_path in files['dockerfiles']:
                dockerfile_name = dockerfile_path.name
                suffix = '' if dockerfile_name == 'Dockerfile' else dockerfile_name.replace('Dockerfile.', '')

                dockerfile_info = {
                    'path': str(dockerfile_path),
                    'name': dockerfile_name,
                    'suffix': suffix
                }
                inventory[folder_key]['dockerfiles'].append(dockerfile_info)

        logging.info(f"Built inventory with {len(inventory)} folders")
        return inventory

    def folder_has_changes(self, folder: Path, changed_files: Set[Path]) -> bool:
        """Check if any file in folder changed"""
        for changed_file in changed_files:
            if changed_file.parent == folder:
                return True
        return False

    def generate_matrix_output(self) -> Dict:
        """Generate the final matrix output"""
        # Get git changes
        self.changed_files, self.deleted_files, self.renamed_files = self.get_changed_files()
        ref_name, commit_sha = self.get_comparison_ref()

        # Discover all files
        discovered = self.discover_files()

        # Build unified inventory
        inventory = self.build_unified_inventory(discovered)

        # Process for output
        all_apps = []
        all_containers = []
        updated_apps = []
        updated_containers = []

        for folder_key, folder_data in inventory.items():
            folder_path = Path(folder_data['path'])
            has_changes = self.folder_has_changes(folder_path, self.changed_files)

            # Apps (if has app_config)
            if folder_data['app_config']:
                app_item = {
                    'path': folder_data['path'],
                    'app_name': folder_data['app_name'],
                    'app_config': folder_data['app_config']
                }
                all_apps.append(app_item)

                if has_changes:
                    updated_apps.append(app_item)
                    logging.info(f"App updated: {folder_data['app_name']}")

            # Containers (for each dockerfile)
            for dockerfile in folder_data['dockerfiles']:
                # Generate container name
                base_name = folder_data['app_name']
                container_name = base_name if not dockerfile['suffix'] else f"{base_name}-{dockerfile['suffix']}"
                container_name = container_name.lower()

                container_item = {
                    'path': folder_data['path'],
                    'context': self.get_dockerfile_context(Path(dockerfile['path'])),
                    'app_name': folder_data['app_name'],
                    'dockerfile': dockerfile,
                    'container_name': container_name
                }
                all_containers.append(container_item)

                if has_changes:
                    updated_containers.append(container_item)
                    logging.info(f"Container updated: {container_name}")

        # Handle deletions
        deleted_apps, deleted_containers = self.analyze_deletions(inventory)

        # Add commit SHA to deleted items
        if commit_sha:
            for item in deleted_apps + deleted_containers:
                item['commit_sha'] = commit_sha

        return {
            'apps': {
                'updated': updated_apps,
                'all': all_apps,
                'deleted': deleted_apps,
                'has_updates': len(updated_apps) > 0,
                'has_deletions': len(deleted_apps) > 0
            },
            'containers': {
                'updated': updated_containers,
                'all': all_containers,
                'deleted': deleted_containers,
                'has_updates': len(updated_containers) > 0,
                'has_deletions': len(deleted_containers) > 0
            },
            'ref': ref_name
        }

    def analyze_deletions(self, inventory: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Analyze deleted files for cleanup"""
        deleted_apps = []
        deleted_containers = []

        # Group deleted files by folder
        deleted_by_folder = {}
        for deleted_file in self.deleted_files:
            if not self.should_include_path(deleted_file):
                continue

            folder = deleted_file.parent
            if folder not in deleted_by_folder:
                deleted_by_folder[folder] = {'app_configs': [], 'dockerfiles': []}

            filename = deleted_file.name
            if filename in ['app.yaml', 'app.yml']:
                deleted_by_folder[folder]['app_configs'].append(deleted_file)
            elif filename == 'Dockerfile' or filename.startswith('Dockerfile.'):
                deleted_by_folder[folder]['dockerfiles'].append(deleted_file)

        # Process deletions
        for folder, deleted_items in deleted_by_folder.items():
            # Determine app name for deleted items
            if folder == Path('.'):
                app_name = self._normalize_azure_name(self.root_path.name)
            else:
                app_name = self._normalize_azure_name(folder.name)

            # Check if folder still exists
            folder_exists = (self.root_path / folder).exists()

            # Handle deleted app configs
            for app_config in deleted_items['app_configs']:
                deleted_apps.append({
                    'path': str(folder),
                    'app_name': app_name,
                    'app_config': str(app_config)
                })

            # Handle deleted dockerfiles
            for dockerfile_path in deleted_items['dockerfiles']:
                dockerfile_name = dockerfile_path.name
                suffix = '' if dockerfile_name == 'Dockerfile' else dockerfile_name.replace('Dockerfile.', '')

                container_name = app_name if not suffix else f"{app_name}-{suffix}"
                container_name = container_name.lower()

                deleted_containers.append({
                    'app_name': app_name,
                    'container_name': container_name,
                    'dockerfile': str(dockerfile_path)
                })

        return deleted_apps, deleted_containers


def check_git_repository():
    """Check if running inside a git repository"""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info("Git repository detected.")
    except Exception:
        logging.warning("Not inside a git repository.")


def configure_git_safe_directory(root_path):
    """Ensure git safe.directory is set"""
    logging.info(f"Current user: {getpass.getuser()}")
    logging.info(f"Current working directory: {os.getcwd()}")

    safe_dir = "/github/workspace"
    try:
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", safe_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"Set git safe.directory: {safe_dir}")
    except Exception as e:
        logging.warning(f"Could not set git safe.directory: {e}")


def main():
    """Main entry point"""
    log_level = logging.DEBUG if os.environ.get('DEBUG') else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr
    )

    parser = argparse.ArgumentParser(description='Analyze git changes for build scope')
    parser.add_argument('--root-path', default=os.environ.get('GITHUB_WORKSPACE', '.'),
                        help='Root path to search for changes')
    parser.add_argument('--include-pattern', help='Pattern for paths to include')
    parser.add_argument('--exclude-pattern', help='Pattern for paths to exclude')
    parser.add_argument('--ref', help='Git ref to compare against')
    parser.add_argument('--output-format', choices=['json', 'github'], default='github',
                        help='Output format')
    parser.add_argument('--mock-git', action='store_true',
                        help='Use mock git data for local testing without a git repo')

    args = parser.parse_args()

    # Change to root path
    os.chdir(args.root_path)

    # Configure git
    configure_git_safe_directory(args.root_path)
    check_git_repository()

    # Run analyzer
    analyzer = BuildScopeAnalyzer(
        root_path=args.root_path,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern,
        mock_git=args.mock_git
    )

    output = analyzer.generate_matrix_output()

    # Output results
    if args.output_format == 'github':
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"matrix={json.dumps(output)}\n")
                f.write(f"ref={output['ref']}\n")
        else:
            print(f"matrix={json.dumps(output)}")
            print(f"ref={output['ref']}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
