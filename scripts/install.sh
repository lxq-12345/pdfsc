#!/bin/bash
# Installation Script - 安装依赖（WSL优先）

# 使用说明：
# ./install.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📦 PDF Smart Converter - Installation"
echo "===================================="

# 检查 Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ python3 not found. Please install Python 3.10+"
    exit 1
fi
echo "✓ Python: $(python3 --version)"

# 选择虚拟环境目录（WSL优先）
if grep -qi "microsoft" /proc/version 2>/dev/null; then
    VENV_DIR="$PROJECT_ROOT/.venv_wsl"
else
    VENV_DIR="$PROJECT_ROOT/.venv"
fi
echo "✓ Virtual env path: $VENV_DIR"

# 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "✓ Virtual environment already exists"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 升级 pip 工具链
echo "✓ Upgrading pip/setuptools/wheel..."
python -m pip install --upgrade pip setuptools wheel

# 安装依赖
echo "✓ Installing dependencies..."
python -m pip install -r "$PROJECT_ROOT/requirements.txt"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy config template: cp config/config.example.yml config/config.yml"
echo "2. Edit config: vim config/config.yml"
echo "3. Run help: python3 src/pdfsc.py --help"
echo "4. D2 flow test: bash scripts/run_d2.sh flow-test"
