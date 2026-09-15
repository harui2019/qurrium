#!/bin/bash
# Run Linter Script for Qurrium Project

CUR_DIR=$(pwd)
UPDATE_DATE=$(date '+%Y-%m-%d %H:%M:%S')
PYPROJECT_FILE="$CUR_DIR/pyproject.toml"
QURRIUM_DIR="$CUR_DIR/qurry"

echo "| Starting Pylint and Ruff linting at $UPDATE_DATE..."

pylint --rcfile "$PYPROJECT_FILE" "$QURRIUM_DIR" > "$CUR_DIR/pylint.log" && echo "| Pylint completed at $UPDATE_DATE." >> "$CUR_DIR/pylint.log"
ruff check --config "$PYPROJECT_FILE" "$QURRIUM_DIR" > "$CUR_DIR/ruff.lint.log" && echo "| Ruff completed at $UPDATE_DATE." >> "$CUR_DIR/ruff.lint.log"

echo "| Linting completed. Logs are saved in pylint.log and ruff.lint.log."