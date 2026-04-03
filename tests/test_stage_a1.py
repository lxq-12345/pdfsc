#!/usr/bin/env python3
"""
阶段A1验收测试脚本

测试项：
1. 配置文件加载
2. 日志输出
3. CLI参数解析（通过导入测试）
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试1：配置文件加载")
    print("=" * 50)

    try:
        from config import ConfigManager

        # 加载默认配置
        config = ConfigManager()
        config.load_default()

        # 测试配置读取
        output_dir = config.get('paths.output_md')
        log_level = config.get('logging.level')
        api_provider = config.get('api.provider')

        print(f"✅ 默认配置加载成功")
        print(f"   输出目录: {output_dir}")
        print(f"   日志级别: {log_level}")
        print(f"   API提供商: {api_provider}")

        # 测试CLI覆盖
        class MockArgs:
            output = "./custom_output"
            verbose = True
            mode = "restore-only"
            image_mode = None
            config = None

        config.load_cli_overrides(MockArgs())
        new_output = config.get('paths.output_md')
        new_level = config.get('logging.level')

        print(f"✅ CLI参数覆盖成功")
        print(f"   覆盖后输出目录: {new_output}")
        print(f"   覆盖后日志级别: {new_level}")

        return True

    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger():
    """测试日志功能"""
    print("\n" + "=" * 50)
    print("测试2：日志输出")
    print("=" * 50)

    try:
        from config import ConfigManager
        from logger import create_logger

        config = ConfigManager()
        config.load_default()

        logger = create_logger(config)

        print("✅ 日志器创建成功")
        print("   测试各级别日志输出：")

        logger.debug("这是DEBUG信息（verbose模式可见）")
        logger.info("这是INFO信息")
        logger.warning("这是WARNING信息")
        logger.error("这是ERROR信息")

        return True

    except Exception as e:
        print(f"❌ 日志测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_capabilities():
    """测试模型能力注册表"""
    print("\n" + "=" * 50)
    print("测试3：模型能力注册表")
    print("=" * 50)

    try:
        from config import ModelCapabilities
        from pathlib import Path

        capabilities = ModelCapabilities()
        registry_file = Path(__file__).parent.parent / 'config' / 'model_capabilities.yml'
        capabilities.load_registry(registry_file)

        # 测试查询
        claude_vision = capabilities.get_vision_support('anthropic', 'claude-sonnet-4-5')
        gpt4_vision = capabilities.get_vision_support('openai', 'gpt-4o')
        qwen_vision = capabilities.get_vision_support('qwen', 'qwen2.5')

        print(f"✅ 模型能力注册表加载成功")
        print(f"   claude-sonnet-4-5 支持视觉: {claude_vision}")
        print(f"   gpt-4o 支持视觉: {gpt4_vision}")
        print(f"   qwen2.5 支持视觉: {qwen_vision}")

        return True

    except Exception as e:
        print(f"❌ 模型能力测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_module_import():
    """测试CLI模块导入"""
    print("\n" + "=" * 50)
    print("测试4：CLI模块导入")
    print("=" * 50)

    try:
        # 直接导入模块（不执行main）
        import pdfsc

        print(f"✅ CLI模块导入成功")
        print(f"   模块路径: {pdfsc.__file__}")
        print(f"   main函数: {pdfsc.main}")

        return True

    except Exception as e:
        print(f"❌ CLI导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 48 + "╗")
    print("║  阶段A1验收测试 - CLI框架与配置           ║")
    print("╚" + "=" * 48 + "╝")
    print()

    results = []

    results.append(("配置加载", test_config_loading()))
    results.append(("日志输出", test_logger()))
    results.append(("模型能力注册表", test_model_capabilities()))
    results.append(("CLI模块导入", test_cli_module_import()))

    print("\n" + "=" * 50)
    print("测试汇总")
    print("=" * 50)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！阶段A1验收成功！")
    else:
        print("⚠️  部分测试失败，需要修复")
    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
