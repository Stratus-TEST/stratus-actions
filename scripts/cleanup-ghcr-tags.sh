#!/bin/bash
# GitHub CLI api
# https://cli.github.com/manual/gh_api

# Function to list package versions for a specific package
list_package_versions() {
  local package_name=$1

  # Parse the repository name and package name
  # Expected format: "repo-name/package-name" (e.g., "stratus-actions/build-scope-analyzer")
  if [ -z "$(echo "$package_name" | grep '/')" ]; then
    echo "Error: Package name must be in the format 'repo-name/package-name'"
    return 1
  fi

  # URL encode the full package name (replace / with %2F)
  local encoded_name=$(echo "$package_name" | sed 's|/|%2F|g')

  echo "Listing versions for package: $package_name"

  # The correct API path format for GitHub Container Registry packages
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "/orgs/Stratus-TEST/packages/container/$encoded_name/versions" | tee versions.json
}

# Function to delete package versions with specific tags
delete_test_versions() {
  local package_name=$1
  local tag_pattern=${2:-"test-sha-*"}  # Default to "test-sha-*" if not provided
  local dry_run=${3:-true}              # Default to dry run mode for safety

  # Parse the repository name and package name
  if [[ $package_name != */* ]]; then
    echo "Error: Package name must be in the format 'repo-name/package-name'"
    return 1
  fi

  # URL encode the full package name
  local encoded_name=$(echo "$package_name" | sed 's|/|%2F|g')

  echo "Looking for versions to delete in package: $package_name with tag pattern: $tag_pattern"

  # Get all versions
  local versions_json=$(gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "/orgs/Stratus-TEST/packages/container/$encoded_name/versions")

  # Parse the JSON to find versions with matching tags
  echo "$versions_json" > versions.json

  # Determine if we're looking for an exact tag match or using a wildcard pattern
  if echo "$tag_pattern" | grep -q '\*'; then
    # Using a wildcard pattern - convert to a regex pattern for jq
    # Replace * with .* for regex
    local search_prefix=$(echo "$tag_pattern" | sed 's/\*//')

    # Find all version IDs with tags starting with the prefix
    local test_version_ids=$(cat versions.json | jq -r --arg prefix "$search_prefix" '.[] |
      select(.metadata.container.tags[] | startswith($prefix)) |
      .id')
  else
    # Exact tag match
    local test_version_ids=$(cat versions.json | jq -r --arg tag "$tag_pattern" '.[] |
      select(.metadata.container.tags[] | . == $tag) |
      .id')
  fi

  # Count the number of versions found
  local count=$(echo "$test_version_ids" | wc -w)

  # Report what we found
  if [ -z "$test_version_ids" ]; then
    echo "No versions found matching tag pattern: $tag_pattern"
    return 0
  else
    echo "Found $count version(s) matching tag pattern: $tag_pattern"

    # Print the versions we found
    echo "Versions to delete:"
    for version_id in $test_version_ids; do
      local tags=$(cat versions.json | jq -r ".[] | select(.id == $version_id) | .metadata.container.tags[]")
      echo "  - Version ID: $version_id, Tags: $tags"
    done

    # Delete the versions if not in dry run mode
    if [ "$dry_run" = "false" ]; then
      echo "Deleting versions..."
      for version_id in $test_version_ids; do
        echo "Deleting version ID: $version_id"
        gh api \
          -X DELETE \
          -H "Accept: application/vnd.github+json" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          "/orgs/Stratus-TEST/packages/container/$encoded_name/versions/$version_id"
        echo "Deleted version ID: $version_id"
      done
      echo "All matching versions deleted"
    else
      echo "DRY RUN: No versions were actually deleted"
      echo "To delete these versions, run: ./temp.sh $package_name $tag_pattern delete"
    fi
  fi
}

# List all container packages in the organization
list_all_packages() {
  echo "Listing all container packages in Stratus-TEST organization..."
  gh api \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "/orgs/Stratus-TEST/packages?package_type=container"
}

# Example usage:
# list_package_versions "stratus-actions/build-scope-analyzer"
# delete_test_versions "stratus-actions/build-scope-analyzer" "test-sha-*" false

# To use this script:
# 1. Run without arguments to list all packages:
#    ./temp.sh
#
# 2. Run with package name to list versions:
#    ./temp.sh stratus-actions/build-scope-analyzer
#
# 3. Run with package name and tag pattern to see what would be deleted (dry run):
#    ./temp.sh stratus-actions/build-scope-analyzer test-sha-*
#    ./temp.sh stratus-actions/build-scope-analyzer test-sha-0109b60
#
# 4. Run with package name, tag pattern and "delete" to actually delete:
#    ./temp.sh stratus-actions/build-scope-analyzer test-sha-* delete
#    ./temp.sh stratus-actions/build-scope-analyzer test-sha-0109b60 delete

# Process command-line arguments
if [ $# -eq 0 ]; then
  list_all_packages
elif [ $# -eq 1 ]; then
  list_package_versions "$1"
elif [ $# -eq 2 ]; then
  # Assume it's a tag pattern and default to dry run
  delete_test_versions "$1" "$2" true
elif [ $# -eq 3 ]; then
  if [ "$3" = "delete" ]; then
    delete_test_versions "$1" "$2" false  # Actually delete
  else
    echo "Error: Third argument must be 'delete'"
    exit 1
  fi
else
  echo "Usage: $0 [package_name] [tag_pattern] [delete]"
  echo ""
  echo "Examples:"
  echo "  $0                                            # List all packages"
  echo "  $0 stratus-actions/build-scope-analyzer       # List all versions"
  echo "  $0 stratus-actions/build-scope-analyzer test-sha-*       # Dry run delete for pattern"
  echo "  $0 stratus-actions/build-scope-analyzer test-sha-0109b60 # Dry run delete for specific tag"
  echo "  $0 stratus-actions/build-scope-analyzer test-sha-* delete # Actually delete matching pattern"
  exit 1
fi