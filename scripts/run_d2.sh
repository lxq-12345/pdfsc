#!/usr/bin/env bash
# D2 diagnosis & repair helper
#
# Usage:
#   ./scripts/run_d2.sh flow-test
#   ./scripts/run_d2.sh convert <input.pdf> [--mode mock|offline|real]
#   ./scripts/run_d2.sh batch <input_dir> [--mode mock|offline|real]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN=""

choose_python() {
  if [[ -x "$PROJECT_ROOT/.venv_wsl/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv_wsl/bin/python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
    return
  fi
  echo "❌ python3 not found, and .venv_wsl/bin/python missing"
  exit 1
}

mode_to_flags() {
  local mode="$1"
  case "$mode" in
    mock)
      echo "--config $PROJECT_ROOT/config/d2_flow.yml"
      ;;
    offline)
      echo "--offline"
      ;;
    real)
      echo ""
      ;;
    *)
      echo "❌ unsupported mode: $mode (use mock|offline|real)"
      exit 1
      ;;
  esac
}

run_flow_test() {
  echo "== D2 flow test =="
  "$PYTHON_BIN" "$PROJECT_ROOT/tests/test_d2_mock_flow.py"
  "$PYTHON_BIN" "$PROJECT_ROOT/tests/test_stage_b2.py"
}

run_convert() {
  local input_pdf="$1"
  local mode="${2:-mock}"
  local flags
  flags="$(mode_to_flags "$mode")"
  echo "== D2 convert =="
  echo "input: $input_pdf"
  echo "mode : $mode"
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC2086
  "$PYTHON_BIN" src/pdfsc.py convert "$input_pdf" $flags
}

run_batch() {
  local input_dir="$1"
  local mode="${2:-mock}"
  local flags
  flags="$(mode_to_flags "$mode")"
  echo "== D2 batch =="
  echo "input: $input_dir"
  echo "mode : $mode"
  cd "$PROJECT_ROOT"
  # shellcheck disable=SC2086
  "$PYTHON_BIN" src/pdfsc.py convert-batch "$input_dir" $flags
}

main() {
  if [[ $# -lt 1 ]]; then
    cat <<EOF
Usage:
  ./scripts/run_d2.sh flow-test
  ./scripts/run_d2.sh convert <input.pdf> [mock|offline|real]
  ./scripts/run_d2.sh batch <input_dir> [mock|offline|real]
EOF
    exit 1
  fi

  choose_python
  local cmd="$1"
  shift

  case "$cmd" in
    flow-test)
      run_flow_test
      ;;
    convert)
      if [[ $# -lt 1 ]]; then
        echo "❌ convert needs <input.pdf>"
        exit 1
      fi
      run_convert "$1" "${2:-mock}"
      ;;
    batch)
      if [[ $# -lt 1 ]]; then
        echo "❌ batch needs <input_dir>"
        exit 1
      fi
      run_batch "$1" "${2:-mock}"
      ;;
    *)
      echo "❌ unknown command: $cmd"
      exit 1
      ;;
  esac
}

main "$@"
