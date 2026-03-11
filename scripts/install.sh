#!/bin/bash
# Installation Script - 安装依赖

# 使用说明：
# ./install.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📦 PDF Smart Converter - Installation"
echo "======================================"

# 检查Python版本
echo "✓ Checking Python version..."
python3 --version

# 创建虚拟环境
echo "✓ Creating virtual environment..."
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "  (Already exists, skipping)"
else
    python3 -m venv "$PROJECT_ROOT/venv"
fi

# 激活虚拟环境
source "$PROJECT_ROOT/venv/bin/activate"

# 升级pip
echo "✓ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# 安装依赖
echo "✓ Installing dependencies..."
pip install -r "$PROJECT_ROOT/requirements.txt"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy config template: cp config/config.example.yml config/config.yml"
echo "2. Edit config: vim config/config.yml (add your API keys)"
echo "3. Test: ./scripts/run.sh --help"
