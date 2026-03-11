#!/bin/bash
# Launcher Script - 启动程序

# 使用说明：
# ./run.sh <input_pdf> [options]
#
# 例子：
# ./run.sh sample.pdf --output ./output
# ./run.sh sample.pdf --image-mode extract
# ./run.sh batch ./pdfs --output ./output

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.10+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

# 激活虚拟环境
source "$PROJECT_ROOT/venv/bin/activate"

# 运行主程序
echo "🚀 Starting PDF Smart Converter..."
cd "$PROJECT_ROOT"
python3 src/pdfsc.py "$@"
