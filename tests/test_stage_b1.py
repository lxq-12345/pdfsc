#!/usr/bin/env python3
"""
阶段B1验收测试脚本

测试内容：
1. 模型能力注册表读取
2. 自动降级逻辑
3. Claude 适配器创建与调用
4. 工厂接口行为
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager, ModelCapabilities
from model_adapter import AnthropicAdapter, ModelAdapterFactory


def build_config(provider='anthropic', model='claude-sonnet-4-5', image_mode='disabled'):
    config = ConfigManager()
    config.load_default()
    config.set('api.provider', provider)
    config.set('api.model', model)
    config.set('images.mode', image_mode)
    return config


def test_capabilities_registry():
    print('=' * 60)
    print('测试1：模型能力注册表读取')
    print('=' * 60)

    registry = ModelCapabilities()
    registry.load_registry(Path(__file__).parent.parent / 'config' / 'model_capabilities.yml')

    known = registry.describe('anthropic', 'claude-sonnet-4-5')
    unknown = registry.describe('anthropic', 'unknown-model')

    print(f"✅ 已知模型 vision: {known['vision']} chinese: {known['chinese']} known: {known['known']}")
    print(f"✅ 未知模型 vision: {unknown['vision']} chinese: {unknown['chinese']} known: {unknown['known']}")

    assert known['vision'] is True
    assert known['known'] is True
    assert unknown['vision'] is False
    assert unknown['known'] is False


def test_auto_downgrade():
    print('\n' + '=' * 60)
    print('测试2：视觉能力自动降级')
    print('=' * 60)

    config = build_config(provider='ollama', model='qwen2.5', image_mode='extract')
    adapter = ModelAdapterFactory.create_from_config(config)

    print(f'✅ 适配器类型: {adapter.__class__.__name__}')
    print(f"✅ 当前图片模式: {config.get('images.mode')}")

    assert config.get('images.mode') == 'disabled'
    assert adapter.check_vision_support() is False


def test_anthropic_call_and_retry():
    print('\n' + '=' * 60)
    print('测试3：Claude 适配器调用与重试')
    print('=' * 60)

    config = build_config(provider='anthropic', model='claude-sonnet-4-5')
    adapter = AnthropicAdapter(config)

    class MockMessages:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError('transient error')
            return SimpleNamespace(
                content=[SimpleNamespace(type='text', text='Claude API response ok')]
            )

    mock_messages = MockMessages()
    mock_client = SimpleNamespace(messages=mock_messages)

    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}, clear=False):
        with patch.object(adapter, '_create_client', return_value=mock_client):
            with patch('model_adapter.time.sleep', return_value=None):
                result = adapter.call('hello world', max_retries=2)

    print(f'✅ Claude 调用结果: {result}')
    print(f'✅ 调用次数: {mock_messages.calls}')

    assert result == 'Claude API response ok'
    assert mock_messages.calls == 2


def test_factory_create_anthropic():
    print('\n' + '=' * 60)
    print('测试4：工厂创建 Claude 适配器')
    print('=' * 60)

    config = build_config()
    adapter = ModelAdapterFactory.create_adapter('anthropic', 'claude-sonnet-4-5', config)

    print(f'✅ 工厂创建成功: {adapter.__class__.__name__}')
    print(f'✅ 模型支持视觉: {adapter.check_vision_support()}')

    assert isinstance(adapter, AnthropicAdapter)
    assert adapter.check_vision_support() is True


def main():
    tests = [
        ('能力注册表', test_capabilities_registry),
        ('自动降级', test_auto_downgrade),
        ('Claude调用与重试', test_anthropic_call_and_retry),
        ('工厂创建', test_factory_create_anthropic),
    ]

    results = []
    for name, func in tests:
        try:
            func()
            results.append((name, True))
        except Exception as exc:
            print(f'❌ {name} 测试失败: {exc}')
            results.append((name, False))

    print('\n' + '=' * 60)
    print('测试汇总')
    print('=' * 60)

    for name, passed in results:
        print(f"{name:20s}: {'✅ 通过' if passed else '❌ 失败'}")

    all_passed = all(passed for _, passed in results)
    print('\n' + '=' * 60)
    if all_passed:
        print('🎉 所有测试通过！阶段B1验收成功！')
    else:
        print('⚠️ 部分测试失败，需要修复')
    print('=' * 60)
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())