#!/usr/bin/env python3
"""
API Key 验证脚本
验证 ANTHROPIC_API_KEY 是否有效
"""
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_adapter import ModelAdapterFactory
from config import ConfigManager


def test_api_key():
    """验证API Key是否有效"""
    print("=" * 60)
    print("API Key 验证测试")
    print("=" * 60)
    print()

    # 1. 检查环境变量
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 错误：未找到环境变量 ANTHROPIC_API_KEY")
        print()
        print("请先设置环境变量：")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return 1

    print(f"✅ 环境变量已设置：ANTHROPIC_API_KEY = {api_key[:12]}...{api_key[-4:]}")
    print()

    # 2. 创建适配器
    print("⏳ 创建Claude适配器...")
    try:
        config = ConfigManager()
        config.load_default()

        adapter = ModelAdapterFactory.create_adapter(
            provider='anthropic',
            model='claude-sonnet-4-5',
            config=config,
            logger=None
        )
        print("✅ 适配器创建成功")
        print()
    except Exception as e:
        print(f"❌ 适配器创建失败: {e}")
        return 1

    # 3. 测试API调用（简单文本）
    print("⏳ 测试API调用（简单文本）...")
    try:
        test_prompt = "请用一句话回答：1+1等于几？"
        response = adapter.call(test_prompt, images=None, max_retries=1)

        print("✅ API调用成功")
        print()
        print("请求：", test_prompt)
        print("响应：", response[:100] + "..." if len(response) > 100 else response)
        print()

    except Exception as e:
        print(f"❌ API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 4. 总结
    print("=" * 60)
    print("✅ API Key 验证通过")
    print("=" * 60)
    print()
    print("下一步：")
    print("  - 可以执行真实API测试（tests/test_stage_b1_real.py）")
    print("  - 可以执行真实PDF转换测试")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(test_api_key())
