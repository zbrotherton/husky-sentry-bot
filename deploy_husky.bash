#!/usr/bin/env bash

set -euo pipefail


# ============================================================================
# Configuration
# ============================================================================

HUSKY_USER="robot"
HUSKY_IP="192.168.131.1"

HUSKY="${HUSKY_USER}@${HUSKY_IP}"
HUSKY_WS="/home/${HUSKY_USER}/husky_ws"


# ============================================================================
# Local paths
#
# This script is expected to live in the project root:
#
# project/
# ├── deploy_husky.sh
# ├── clearpath/
# │   └── robot.yaml
# └── src/
#     └── sentry_description/
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DESCRIPTION_DIR="${PROJECT_ROOT}/src/sentry_description"
ROBOT_YAML="${PROJECT_ROOT}/clearpath/robot.yaml"


# ============================================================================
# Validate local files
# ============================================================================

echo "=== Validating deployment files ==="

if [[ ! -d "${DESCRIPTION_DIR}" ]]; then
    echo "ERROR: sentry_description not found:"
    echo "  ${DESCRIPTION_DIR}"
    exit 1
fi

if [[ ! -f "${DESCRIPTION_DIR}/package.xml" ]]; then
    echo "ERROR: sentry_description does not contain package.xml"
    exit 1
fi

if [[ ! -f "${ROBOT_YAML}" ]]; then
    echo "ERROR: robot.yaml not found:"
    echo "  ${ROBOT_YAML}"
    exit 1
fi

echo "Project root:"
echo "  ${PROJECT_ROOT}"
echo
echo "Description:"
echo "  ${DESCRIPTION_DIR}"
echo
echo "Robot configuration:"
echo "  ${ROBOT_YAML}"


# ============================================================================
# Prepare remote workspace
# ============================================================================

echo
echo "=== Preparing Husky workspace ==="

ssh "${HUSKY}" \
    "mkdir -p '${HUSKY_WS}/src/sentry_description'"


# ============================================================================
# Deploy sentry_description
# ============================================================================

echo
echo "=== Deploying sentry_description ==="

rsync -av --delete \
    "${DESCRIPTION_DIR}/" \
    "${HUSKY}:${HUSKY_WS}/src/sentry_description/"


# ============================================================================
# Build sentry_description
# ============================================================================

echo
echo "=== Building sentry_description on Husky ==="

ssh "${HUSKY}" "
    source /opt/ros/jazzy/setup.bash &&
    cd '${HUSKY_WS}' &&
    colcon build \
        --packages-select sentry_description \
        --symlink-install
"


# ============================================================================
# Upload new robot.yaml
#
# It is uploaded to /tmp first because the normal SSH user should not need
# direct write access to /etc/clearpath.
# ============================================================================

echo
echo "=== Uploading robot.yaml ==="

rsync -av \
    "${ROBOT_YAML}" \
    "${HUSKY}:/tmp/robot.yaml"


# ============================================================================
# Install configuration and restart Clearpath
# ============================================================================

echo
echo "=== Installing Clearpath configuration ==="
echo
echo "The currently installed robot.yaml will be saved as:"
echo "  /etc/clearpath/robot.yaml.backup"
echo
echo "Only ONE backup is retained."
echo "The previous backup will be replaced by the configuration"
echo "that is currently installed."
echo
echo "You may be prompted for the Husky sudo password."
echo

ssh -t "${HUSKY}" "
    set -e

    # Authenticate sudo before making any system changes.
    sudo -v

    echo
    echo 'Backing up current Clearpath configuration...'

    if [ -f /etc/clearpath/robot.yaml ]; then
        sudo cp \
            /etc/clearpath/robot.yaml \
            /etc/clearpath/robot.yaml.backup

        echo 'Backup created:'
        echo '  /etc/clearpath/robot.yaml.backup'
    else
        echo 'No existing /etc/clearpath/robot.yaml found.'
        echo 'No backup was created.'
    fi

    echo
    echo 'Installing new robot.yaml...'

    sudo install \
        -m 0644 \
        /tmp/robot.yaml \
        /etc/clearpath/robot.yaml

    rm -f /tmp/robot.yaml

    echo
    echo 'Restarting clearpath-robot.service...'

    sudo systemctl restart clearpath-robot.service

    echo
    echo 'Checking Clearpath service status...'

    if sudo systemctl is-active --quiet clearpath-robot.service; then
        echo 'clearpath-robot.service is ACTIVE.'
    else
        echo 'ERROR: clearpath-robot.service failed to become active.'
        echo
        sudo systemctl status \
            clearpath-robot.service \
            --no-pager
        exit 1
    fi
"


# ============================================================================
# Complete
# ============================================================================

echo
echo "============================================================"
echo " Husky deployment complete"
echo "============================================================"
echo
echo "Deployed:"
echo "  sentry_description -> ${HUSKY_WS}/src/sentry_description"
echo "  robot.yaml         -> /etc/clearpath/robot.yaml"
echo
echo "Previous configuration:"
echo "  /etc/clearpath/robot.yaml.backup"
echo
echo "Clearpath service:"
echo "  clearpath-robot.service: restarted successfully"
echo