#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Description:
#   This script updates the Google Ads API Developer Assistant and its dependencies.
#   It performs the following steps:
#   1. Updates the 'google-ads-api-developer-assistant' repository (git pull).
#   2. Reads '.gemini/settings.json' to locate the 'google-ads-python' repository.
#   3. Updates the 'google-ads-python' repository (git pull).

# Exit on any error, and on undefined variables.
set -eu

# Function to print errors to stderr
err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

# --- Dependency Check ---
if ! command -v jq &> /dev/null; then
  err "ERROR: jq is not installed. Please install it to continue."
  err "See: https://jqlang.github.io/jq/download/"
  exit 1
fi
if ! command -v git &> /dev/null; then
  err "ERROR: git is not installed. Please install it to continue."
  exit 1
fi

# --- Project Directory Resolution ---
# Determine the root directory of the current git repository.
if ! PROJECT_DIR_ABS=$(git rev-parse --show-toplevel 2>/dev/null); then
  err "ERROR: This script must be run from within the google-ads-api-developer-assistant git repository."
  exit 1
fi
readonly PROJECT_DIR_ABS
echo "Detected project root: ${PROJECT_DIR_ABS}"

# --- Update Assistant Repo ---
echo "Updating google-ads-api-developer-assistant..."
if ! git pull; then
    err "ERROR: Failed to update google-ads-api-developer-assistant."
    exit 1
fi
echo "Successfully updated google-ads-api-developer-assistant."

# --- Locate and Update Python Lib ---
readonly SETTINGS_FILE="${PROJECT_DIR_ABS}/.gemini/settings.json"

if [[ ! -f "${SETTINGS_FILE}" ]]; then
  err "ERROR: Settings file not found: ${SETTINGS_FILE}"
  err "Please run setup.sh first."
  exit 1
fi

echo "Reading ${SETTINGS_FILE} to find google-ads-python..."

# Extract the path ending with 'google-ads-python' from includeDirectories
PYTHON_LIB_PATH=$(jq -r '.context.includeDirectories[] | select(endswith("google-ads-python"))' "${SETTINGS_FILE}")

if [[ -z "${PYTHON_LIB_PATH}" ]]; then
    err "ERROR: Could not find google-ads-python path in ${SETTINGS_FILE}."
    exit 1
fi

echo "Found google-ads-python at: ${PYTHON_LIB_PATH}"

if [[ ! -d "${PYTHON_LIB_PATH}" ]]; then
    err "ERROR: Directory not found: ${PYTHON_LIB_PATH}"
    exit 1
fi

echo "Updating google-ads-python..."
# Use a subshell to change directory and pull, so we don't affect the current script's CWD
if ! (cd "${PYTHON_LIB_PATH}" && git pull); then
    err "ERROR: Failed to update google-ads-python at ${PYTHON_LIB_PATH}"
    exit 1
fi

echo "Successfully updated google-ads-python."
echo "Update complete."
