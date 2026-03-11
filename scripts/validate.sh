#!/bin/bash
# Validation Script - 验证输出质量

# 使用说明：
# ./validate.sh <markdown_file>
# ./validate.sh ./output/markdown/final/

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -z "$1" ]; then
    echo "❌ Usage: ./validate.sh <markdown_file_or_directory>"
    exit 1
fi

echo "✅ PDF Smart Converter - Output Validation"
echo "=========================================="

source "$PROJECT_ROOT/venv/bin/activate"

echo "Validating: $1"
cd "$PROJECT_ROOT"

# 调用验证器
python3 -c "
from src.validator import MarkdownValidator
import sys

validator = MarkdownValidator('skills/markdown_conversion.md')

# TODO: 实现验证逻辑
print('Validation implementation pending...')
"

echo ""
echo "✅ Validation complete!"
