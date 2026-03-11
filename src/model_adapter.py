"""
Multi-Model Adapter Layer

统一的多模型适配接口，支持Claude/GPT-4o/Qwen/Ollama
"""


class BaseModelAdapter:
    """模型适配器基类"""

    def __init__(self, config):
        """初始化适配器"""
        self.config = config

    def call(self, prompt, images=None, max_retries=3):
        """
        调用模型

        Args:
            prompt: 提示词
            images: 图片列表（可选）
            max_retries: 最大重试次数

        Returns:
            str: 模型输出
        """
        raise NotImplementedError()

    def check_vision_support(self):
        """
        检查模型是否支持视觉（多模态）

        Returns:
            bool: 是否支持视觉
        """
        raise NotImplementedError()


class ModelAdapterFactory:
    """模型适配器工厂"""

    @staticmethod
    def create_adapter(provider, model, config):
        """
        创建适配器

        Args:
            provider: 'anthropic' | 'openai' | 'qwen' | 'ollama'
            model: 模型名称
            config: 配置对象

        Returns:
            BaseModelAdapter: 对应的适配器实例
        """
        raise NotImplementedError()


class AnthropicAdapter(BaseModelAdapter):
    """Claude API 适配器"""
    pass


class OpenAIAdapter(BaseModelAdapter):
    """OpenAI API 适配器"""
    pass


class QwenAdapter(BaseModelAdapter):
    """阿里Qwen API 适配器"""
    pass


class OllamaAdapter(BaseModelAdapter):
    """Ollama 本地模型适配器"""
    pass
