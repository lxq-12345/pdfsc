"""
Configuration Management Module

加载和管理所有配置（三层次）
"""

import yaml
from pathlib import Path


class ConfigManager:
    """配置管理器"""

    def __init__(self, project_root=None):
        """初始化配置管理器"""
        self.project_root = project_root or Path(__file__).parent.parent
        self.config = {}

    def load_default(self):
        """加载默认配置"""
        default_yml = self.project_root / 'config' / 'default.yml'
        raise NotImplementedError()

    def load_user(self, config_file=None):
        """加载用户配置"""
        raise NotImplementedError()

    def load_cli_overrides(self, cli_args):
        """加载命令行参数覆盖"""
        raise NotImplementedError()

    def get(self, key, default=None):
        """获取配置值"""
        raise NotImplementedError()

    def save_user_config(self, config_file):
        """保存用户配置到文件"""
        raise NotImplementedError()


class ModelCapabilities:
    """模型能力注册表"""

    def __init__(self):
        """初始化能力注册表"""
        self.capabilities = {}

    def load_registry(self, registry_file):
        """加载能力注册表"""
        raise NotImplementedError()

    def get_vision_support(self, provider, model):
        """
        查询模型是否支持视觉

        Args:
            provider: 'anthropic' | 'openai' | 'qwen' | 'ollama'
            model: 模型名称

        Returns:
            bool: 是否支持视觉（None表示未知，保守降级）
        """
        raise NotImplementedError()

    def get_chinese_support(self, provider, model):
        """
        查询模型是否支持中文

        Returns:
            bool
        """
        raise NotImplementedError()
