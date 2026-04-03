"""
Multi-Model Adapter Layer

统一的多模型适配接口，优先实现 Claude API 接入，
并为 OpenAI/Qwen/Ollama 保留兼容调用能力。
"""

import base64
import mimetypes
import os
import time
from pathlib import Path

from config import ModelCapabilities

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class BaseModelAdapter:
    """模型适配器基类"""

    default_key_env = None
    default_base_url = None

    def __init__(self, config, provider=None, model=None, logger=None, capabilities=None, api_config=None):
        """初始化适配器"""
        self.config = config
        self.logger = logger
        self.api_config = api_config or self._load_api_config()

        if provider:
            self.api_config['provider'] = provider
        if model:
            self.api_config['model'] = model

        self.provider = self.api_config.get('provider')
        self.model = self.api_config.get('model')
        self.key_env = self.api_config.get('key_env') or self.default_key_env
        self.base_url = self.api_config.get('base_url') or self.default_base_url
        self.timeout = self.api_config.get('timeout', 120)
        self.max_retries = self.api_config.get('max_retries', 3)
        self.max_tokens = self.api_config.get('max_tokens', 4096)
        self.unknown_model_vision = self.api_config.get('unknown_model_vision', False)
        self.capabilities = capabilities or self._load_capabilities()

        if not self.provider or not self.model:
            raise ValueError('API provider/model 未配置，无法创建模型适配器')

    def call(self, prompt, images=None, max_retries=None):
        """调用模型"""
        raise NotImplementedError()

    def check_vision_support(self):
        """检查模型是否支持视觉（多模态）"""
        return bool(
            self.capabilities.get_vision_support(
                self.provider,
                self.model,
                unknown_default=self.unknown_model_vision,
            )
        )

    def apply_capability_guard(self):
        """当模型不支持视觉时，自动降级为纯文字模式。"""
        image_mode = self._get_config_value('images.mode', 'disabled')
        if image_mode == 'disabled':
            return False

        if self.check_vision_support():
            return False

        self._set_config_value('images.mode', 'disabled')
        self._warn(
            f"当前模型 {self.model} 不支持视觉，图片模式已自动切换为 disabled。"
        )
        return True

    def _load_api_config(self):
        if hasattr(self.config, 'get_api_config'):
            return dict(self.config.get_api_config())
        return dict(self._get_config_value('api', {}))

    def _get_config_value(self, key, default=None):
        if isinstance(self.config, dict):
            value = self.config
            for part in key.split('.'):
                if not isinstance(value, dict):
                    return default
                value = value.get(part)
            return value if value is not None else default

        if hasattr(self.config, 'get'):
            return self.config.get(key, default)

        return default

    def _set_config_value(self, key, value):
        if isinstance(self.config, dict):
            target = self.config
            parts = key.split('.')
            for part in parts[:-1]:
                if part not in target or not isinstance(target[part], dict):
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
            return

        if hasattr(self.config, 'set'):
            self.config.set(key, value)

    def _load_capabilities(self):
        registry = self._get_project_root() / 'config' / 'model_capabilities.yml'
        capabilities = ModelCapabilities()
        capabilities.load_registry(registry)
        return capabilities

    def _get_project_root(self):
        if hasattr(self.config, 'project_root'):
            return Path(self.config.project_root)
        return Path(__file__).resolve().parent.parent

    def _resolve_api_key(self, required=True):
        if not self.key_env:
            if required:
                raise ValueError(f'{self.provider} 模型缺少 key_env 配置')
            return None

        api_key = os.getenv(self.key_env)
        if required and not api_key:
            raise ValueError(f'环境变量 {self.key_env} 未设置，无法调用 {self.provider} 模型')
        return api_key

    def _prepare_images(self, images):
        if not images:
            return []

        if not self.check_vision_support():
            self.apply_capability_guard()
            return []

        if isinstance(images, (str, Path, bytes, bytearray, dict)):
            return [images]

        return list(images)

    def _encode_image(self, image):
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            image_bytes = image_path.read_bytes()
            media_type = mimetypes.guess_type(str(image_path))[0] or 'image/png'
            return media_type, base64.b64encode(image_bytes).decode('utf-8')

        if isinstance(image, (bytes, bytearray)):
            return 'image/png', base64.b64encode(bytes(image)).decode('utf-8')

        if isinstance(image, dict):
            if 'path' in image:
                return self._encode_image(image['path'])
            if 'base64' in image:
                return image.get('media_type', 'image/png'), image['base64']
            if 'data' in image:
                data = image['data']
                if isinstance(data, str):
                    data = data.encode('utf-8')
                return image.get('media_type', 'image/png'), base64.b64encode(data).decode('utf-8')

        raise TypeError(f'不支持的图片输入类型: {type(image)!r}')

    def _warn(self, message):
        if self.logger and hasattr(self.logger, 'warning'):
            self.logger.warning(message)
            return
        print(f'[WARNING] {message}')

    def _retry_delay(self, attempt_index):
        return min(2 ** attempt_index, 4)


class ModelAdapterFactory:
    """模型适配器工厂"""

    ADAPTER_MAP = {
        'anthropic': lambda *args, **kwargs: AnthropicAdapter(*args, **kwargs),
        'openai': lambda *args, **kwargs: OpenAIAdapter(*args, **kwargs),
        'qwen': lambda *args, **kwargs: QwenAdapter(*args, **kwargs),
        'ollama': lambda *args, **kwargs: OllamaAdapter(*args, **kwargs),
    }

    @staticmethod
    def create_adapter(provider, model, config, logger=None, capabilities=None, api_config=None):
        """创建适配器实例并应用能力保护。"""
        provider_key = provider.lower()
        if provider_key not in ModelAdapterFactory.ADAPTER_MAP:
            raise ValueError(f'不支持的模型提供商: {provider}')

        adapter = ModelAdapterFactory.ADAPTER_MAP[provider_key](
            config=config,
            provider=provider_key,
            model=model,
            logger=logger,
            capabilities=capabilities,
            api_config=api_config,
        )
        adapter.apply_capability_guard()
        return adapter

    @staticmethod
    def create_from_config(config, logger=None, pdf_type=None, capabilities=None):
        """从配置对象直接创建适配器。"""
        if hasattr(config, 'get_api_config'):
            api_config = config.get_api_config(pdf_type)
        else:
            api_config = config.get('api', {}) if isinstance(config, dict) else {}

        provider = api_config.get('provider')
        model = api_config.get('model')
        return ModelAdapterFactory.create_adapter(
            provider=provider,
            model=model,
            config=config,
            logger=logger,
            capabilities=capabilities,
            api_config=api_config,
        )


class AnthropicAdapter(BaseModelAdapter):
    """Claude API 适配器"""

    default_key_env = 'ANTHROPIC_API_KEY'

    def _create_client(self):
        if Anthropic is None:
            raise ImportError('anthropic 未安装，无法调用 Claude API')

        client_kwargs = {
            'api_key': self._resolve_api_key(required=True),
            'timeout': self.timeout,
        }
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
        return Anthropic(**client_kwargs)

    def _build_content(self, prompt, images):
        content = []
        for image in images:
            media_type, base64_data = self._encode_image(image)
            content.append(
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': base64_data,
                    },
                }
            )
        content.append({'type': 'text', 'text': prompt})
        return content

    def _extract_text(self, response):
        parts = []
        for block in getattr(response, 'content', []) or []:
            block_type = getattr(block, 'type', None)
            block_text = getattr(block, 'text', None)
            if block_type == 'text' and block_text:
                parts.append(block_text)
        return ''.join(parts).strip()

    def call(self, prompt, images=None, max_retries=None):
        retries = max_retries or self.max_retries
        prepared_images = self._prepare_images(images)
        client = self._create_client()
        last_error = None

        for attempt in range(retries):
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {
                            'role': 'user',
                            'content': self._build_content(prompt, prepared_images),
                        }
                    ],
                )
                text = self._extract_text(response)
                if not text:
                    raise ValueError('Claude 返回为空')
                return text
            except Exception as exc:
                last_error = exc
                if attempt == retries - 1:
                    break
                time.sleep(self._retry_delay(attempt))

        raise RuntimeError(
            f'Claude API 调用失败（provider={self.provider}, model={self.model}）: {last_error}'
        ) from last_error


class OpenAICompatibleAdapter(BaseModelAdapter):
    """兼容 OpenAI Chat Completions 的适配器基类"""

    def _create_client(self, require_api_key=True):
        if OpenAI is None:
            raise ImportError('openai 未安装，无法调用兼容接口模型')

        api_key = self._resolve_api_key(required=require_api_key)
        client_kwargs = {
            'api_key': api_key or 'ollama',
        }
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
        return OpenAI(**client_kwargs)

    def _build_content(self, prompt, images):
        content = [{'type': 'text', 'text': prompt}]
        for image in images:
            media_type, base64_data = self._encode_image(image)
            content.append(
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:{media_type};base64,{base64_data}',
                    },
                }
            )
        return content

    def _extract_text(self, response):
        choices = getattr(response, 'choices', None) or []
        if not choices:
            return ''

        message = getattr(choices[0], 'message', None)
        if message is None:
            return ''

        content = getattr(message, 'content', '')
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    parts.append(item.get('text', ''))
            return ''.join(parts).strip()

        return ''

    def call(self, prompt, images=None, max_retries=None):
        retries = max_retries or self.max_retries
        prepared_images = self._prepare_images(images)
        client = self._create_client(require_api_key=self.provider != 'ollama')
        last_error = None

        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            'role': 'user',
                            'content': self._build_content(prompt, prepared_images),
                        }
                    ],
                    timeout=self.timeout,
                )
                text = self._extract_text(response)
                if not text:
                    raise ValueError(f'{self.provider} 返回为空')
                return text
            except Exception as exc:
                last_error = exc
                if attempt == retries - 1:
                    break
                time.sleep(self._retry_delay(attempt))

        raise RuntimeError(
            f'{self.provider} 模型调用失败（model={self.model}）: {last_error}'
        ) from last_error


class OpenAIAdapter(OpenAICompatibleAdapter):
    """OpenAI API 适配器"""

    default_key_env = 'OPENAI_API_KEY'


class QwenAdapter(OpenAICompatibleAdapter):
    """阿里 Qwen API 适配器"""

    default_key_env = 'DASHSCOPE_API_KEY'
    default_base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'


class OllamaAdapter(OpenAICompatibleAdapter):
    """Ollama 本地模型适配器"""

    default_base_url = 'http://localhost:11434/v1'
