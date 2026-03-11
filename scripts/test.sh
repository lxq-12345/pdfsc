#!/bin/bash
# Test Script - 运行测试

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 PDF Smart Converter - Testing"
echo "=================================="

source "$PROJECT_ROOT/venv/bin/activate"

echo "✓ Running tests..."
cd "$PROJECT_ROOT"

# 检查代码风格（可选）
# python3 -m pylint src/

# 运行单元测试
echo "  - Unit tests..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v
else
    echo "  ⚠️  pytest not installed, skipping unit tests"
fi

echo ""
echo "✅ Tests complete!"
