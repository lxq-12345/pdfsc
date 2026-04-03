#!/usr/bin/env python3
"""
Step0-6 验证：瓶颈6——多模型适配兼容性

验证目标：
- 切换模型时输出格式一致
- 图片输入格式适配正确
- 错误处理正常

测试方式：Mock模式（无需真实API Key）
"""
import sys
import os
import base64
import io
from unittest.mock import Mock, patch, MagicMock

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_adapter import AnthropicAdapter, QwenAdapter, OllamaAdapter
from config import ModelCapabilities


def create_test_capabilities():
    """创建测试用的 ModelCapabilities 对象"""
    capabilities = ModelCapabilities()
    # 加载默认配置
    registry_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'model_capabilities.yml'
    )
    if os.path.exists(registry_path):
        capabilities.load_registry(registry_path)
    return capabilities


def create_test_image():
    """创建测试用的最小PNG图片（1x1像素）"""
    # 最小的1x1透明PNG图片
    png_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=='
    return base64.b64decode(png_base64)


def test_anthropic_adapter():
    """测试 AnthropicAdapter 请求格式构造"""
    print("📋 测试 AnthropicAdapter...")

    # 创建适配器
    config = {'api': {'key_env': 'ANTHROPIC_API_KEY'}}
    capabilities = create_test_capabilities()
    adapter = AnthropicAdapter(
        config=config,
        provider='anthropic',
        model='claude-sonnet-4-5',
        logger=None,
        capabilities=capabilities
    )

    # Mock Anthropic client
    mock_response = Mock()
    mock_response.content = [Mock(type='text', text='测试返回内容')]

    mock_client = Mock()
    mock_client.messages.create.return_value = mock_response

    # 测试1: 纯文本请求
    with patch.object(adapter, '_create_client', return_value=mock_client):
        result = adapter.call("测试提示词", images=None)

        # 验证调用参数
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs['model'] == 'claude-sonnet-4-5'
        messages = call_args.kwargs['messages']
        assert len(messages) == 1
        assert messages[0]['role'] == 'user'

        content = messages[0]['content']
        assert isinstance(content, list)
        assert any(item['type'] == 'text' for item in content)

        print("  ✅ 纯文本请求格式正确")

    # 测试2: 图片+文本请求
    test_image = create_test_image()

    with patch.object(adapter, '_create_client', return_value=mock_client):
        result = adapter.call("测试提示词", images=[test_image])

        call_args = mock_client.messages.create.call_args
        content = call_args.kwargs['messages'][0]['content']

        # 验证图片格式
        has_image = False
        has_text = False
        for item in content:
            if item['type'] == 'image':
                has_image = True
                assert 'source' in item
                assert item['source']['type'] == 'base64'
                assert 'media_type' in item['source']
                assert 'data' in item['source']
            elif item['type'] == 'text':
                has_text = True

        assert has_image, "请求中应包含图片"
        assert has_text, "请求中应包含文本"
        print("  ✅ 图片+文本请求格式正确")

    # 测试3: 错误重试
    # 创建新的 mock 对象以避免 call_count 累积
    mock_retry_response = Mock()
    mock_retry_response.content = [Mock(type='text', text='测试返回内容')]

    mock_retry_client = Mock()
    mock_retry_client.messages.create.side_effect = [
        Exception("模拟网络错误"),
        Exception("模拟超时"),
        mock_retry_response  # 第3次成功
    ]

    with patch.object(adapter, '_create_client', return_value=mock_retry_client):
        with patch('time.sleep'):  # 跳过真实sleep
            result = adapter.call("测试提示词", max_retries=3)
            assert result == "测试返回内容"
            assert mock_retry_client.messages.create.call_count == 3
            print("  ✅ 错误重试机制正常")

    print("✅ AnthropicAdapter 验证通过\n")


def test_openai_compatible_adapters():
    """测试 OpenAI 兼容适配器（Qwen / Ollama）"""
    providers = [
        ('qwen', QwenAdapter, 'qwen-vl-max'),
        ('ollama', OllamaAdapter, 'qwen2.5-vl'),
    ]

    for provider_name, AdapterClass, model_name in providers:
        print(f"📋 测试 {AdapterClass.__name__}...")

        config = {
            'api': {
                'base_url': 'http://test.example.com/v1' if provider_name == 'qwen' else 'http://localhost:11434/v1',
                'key_env': 'DASHSCOPE_API_KEY' if provider_name == 'qwen' else None
            }
        }

        capabilities = create_test_capabilities()
        adapter = AdapterClass(
            config=config,
            provider=provider_name,
            model=model_name,
            logger=None,
            capabilities=capabilities
        )

        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='测试返回内容'))
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        # 测试1: 纯文本请求
        with patch.object(adapter, '_create_client', return_value=mock_client):
            result = adapter.call("测试提示词", images=None)

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['model'] == model_name
            messages = call_args.kwargs['messages']
            assert len(messages) == 1
            assert messages[0]['role'] == 'user'

            content = messages[0]['content']
            assert isinstance(content, list)
            assert any(item['type'] == 'text' for item in content)

            print(f"  ✅ 纯文本请求格式正确")

        # 测试2: 图片+文本请求
        test_image = create_test_image()

        with patch.object(adapter, '_create_client', return_value=mock_client):
            result = adapter.call("测试提示词", images=[test_image])

            call_args = mock_client.chat.completions.create.call_args
            content = call_args.kwargs['messages'][0]['content']

            # 验证OpenAI格式的图片
            has_image = False
            has_text = False
            for item in content:
                if item['type'] == 'image_url':
                    has_image = True
                    assert 'image_url' in item
                    assert 'url' in item['image_url']
                    assert item['image_url']['url'].startswith('data:image/')
                elif item['type'] == 'text':
                    has_text = True

            assert has_image, "请求中应包含图片"
            assert has_text, "请求中应包含文本"
            print(f"  ✅ 图片+文本请求格式正确（OpenAI格式）")

        # 测试3: 错误重试
        # 创建新的 mock 对象以避免 call_count 累积
        mock_retry_response = Mock()
        mock_retry_response.choices = [
            Mock(message=Mock(content='测试返回内容'))
        ]

        mock_retry_client = Mock()
        mock_retry_client.chat.completions.create.side_effect = [
            Exception("模拟网络错误"),
            mock_retry_response  # 第2次成功
        ]

        with patch.object(adapter, '_create_client', return_value=mock_retry_client):
            with patch('time.sleep'):
                result = adapter.call("测试提示词", max_retries=2)
                assert result == "测试返回内容"
                assert mock_retry_client.chat.completions.create.call_count == 2
                print(f"  ✅ 错误重试机制正常")

        print(f"✅ {AdapterClass.__name__} 验证通过\n")


def test_format_consistency():
    """测试切换模型时输出格式一致性"""
    print("📋 测试输出格式一致性...")

    test_prompt = "测试提示词"
    test_image = create_test_image()
    expected_output = "统一的输出内容"

    # Mock所有适配器返回相同内容
    adapters = [
        ('anthropic', AnthropicAdapter, 'claude-sonnet-4-5'),
        ('qwen', QwenAdapter, 'qwen-vl-max'),
        ('ollama', OllamaAdapter, 'qwen2.5-vl'),
    ]

    results = []

    for provider, AdapterClass, model in adapters:
        config = {'api': {'base_url': 'http://test.example.com'}}
        capabilities = create_test_capabilities()
        adapter = AdapterClass(
            config=config,
            provider=provider,
            model=model,
            logger=None,
            capabilities=capabilities
        )

        # Mock返回
        if provider == 'anthropic':
            mock_response = Mock()
            mock_response.content = [Mock(type='text', text=expected_output)]
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_response
        else:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=expected_output))]
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response

        with patch.object(adapter, '_create_client', return_value=mock_client):
            result = adapter.call(test_prompt, images=[test_image])
            results.append(result)

    # 验证所有输出一致
    assert all(r == expected_output for r in results), "所有适配器应返回一致的内容"
    print(f"  ✅ 3个适配器输出格式一致")
    print("✅ 格式一致性验证通过\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Step0-6 验证：多模型适配兼容性")
    print("测试方式：Mock模式（无需真实API Key）")
    print("=" * 60)
    print()

    try:
        # 测试1: AnthropicAdapter
        test_anthropic_adapter()

        # 测试2: OpenAI兼容适配器
        test_openai_compatible_adapters()

        # 测试3: 格式一致性
        test_format_consistency()

        print("=" * 60)
        print("✅ Step0-6 验证全部通过")
        print("=" * 60)
        print()
        print("验收结论：")
        print("  ✅ 3个适配器（Anthropic/Qwen/Ollama）请求格式正确")
        print("  ✅ 图片输入格式符合各API规范")
        print("  ✅ 文本提取逻辑正确")
        print("  ✅ 错误重试机制正常")
        print("  ✅ 切换模型时输出格式一致")
        print()
        return 0

    except AssertionError as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
