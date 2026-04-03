"""
Configuration Management Module

加载和管理所有配置（三层次）
"""

from copy import deepcopy
from pathlib import Path

import yaml


class ConfigManager:
    """配置管理器"""

    def __init__(self, project_root=None):
        """初始化配置管理器"""
        self.project_root = project_root or Path(__file__).parent.parent
        self.config = {}

    def load_default(self):
        """加载默认配置"""
        default_yml = self.project_root / 'config' / 'default.yml'
        if default_yml.exists():
            with open(default_yml, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Default config not found: {default_yml}")
        return self.config

    def load_user(self, config_file=None):
        """加载用户配置，覆盖默认配置"""
        if config_file:
            user_yml = Path(config_file)
            if user_yml.exists():
                with open(user_yml, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    self._merge_config(user_config)
        return self.config

    def load_cli_overrides(self, cli_args):
        """加载命令行参数覆盖"""
        # 映射CLI参数到配置字段
        cli_mapping = {
            'output': ('paths', 'output_md'),
            'mode': ('conversion', 'mode'),
            'image_mode': ('images', 'mode'),
            'verbose': ('logging', 'level'),  # verbose=True -> DEBUG
            'offline': ('api', 'offline_mode'),
        }

        for cli_key, config_path in cli_mapping.items():
            if hasattr(cli_args, cli_key):
                cli_value = getattr(cli_args, cli_key)
                if cli_value is not None:
                    if cli_key == 'verbose' and cli_value:
                        self._set_nested(config_path, 'DEBUG')
                    else:
                        self._set_nested(config_path, cli_value)
        return self.config

    def get(self, key, default=None):
        """获取配置值，支持点分路径"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        """设置配置值，支持点分路径"""
        keys = key.split('.')
        target = self.config

        for part in keys[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]

        target[keys[-1]] = value

    def get_api_config(self, pdf_type=None):
        """获取生效的 API 配置，按需叠加 type_overrides。"""
        api_config = deepcopy(self.get('api', {}))
        overrides = api_config.pop('type_overrides', {}) or {}

        if pdf_type and pdf_type in overrides:
            self._deep_merge_dicts(api_config, overrides[pdf_type])

        return api_config

    def save_user_config(self, config_file):
        """保存用户配置到文件"""
        config_path = Path(config_file)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)

    def _merge_config(self, user_config):
        """递归合并配置"""
        self._deep_merge_dicts(self.config, user_config)

    def _deep_merge_dicts(self, base, override):
        """递归合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_dicts(base[key], value)
            else:
                base[key] = value

    def _set_nested(self, path, value):
        """设置嵌套配置值"""
        if len(path) == 1:
            self.config[path[0]] = value
        else:
            section, key = path
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value


class ModelCapabilities:
    """模型能力注册表"""

    def __init__(self):
        """初始化能力注册表"""
        self.capabilities = {}

    def load_registry(self, registry_file):
        """加载能力注册表"""
        registry_path = Path(registry_file)
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                self.capabilities = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Model capabilities registry not found: {registry_path}")

    def get_model_info(self, provider, model):
        """获取模型能力信息，未知模型返回 None。"""
        provider_models = self.capabilities.get(provider, {}) or {}
        return provider_models.get(model)

    def get_vision_support(self, provider, model, unknown_default=None):
        """
        查询模型是否支持视觉

        Args:
            provider: 'anthropic' | 'openai' | 'qwen' | 'ollama'
            model: 模型名称

        Returns:
            bool: 是否支持视觉（None表示未知，保守降级）
        """
        model_info = self.get_model_info(provider, model)
        if model_info is None:
            return unknown_default
        return model_info.get('vision', unknown_default)

    def get_chinese_support(self, provider, model, unknown_default=True):
        """
        查询模型是否支持中文

        Returns:
            bool
        """
        model_info = self.get_model_info(provider, model)
        if model_info is None:
            return unknown_default
        return model_info.get('chinese', unknown_default)

    def describe(self, provider, model, unknown_vision=False, unknown_chinese=True):
        """返回统一格式的模型能力描述。"""
        model_info = self.get_model_info(provider, model)
        return {
            'provider': provider,
            'model': model,
            'known': model_info is not None,
            'vision': self.get_vision_support(provider, model, unknown_vision),
            'chinese': self.get_chinese_support(provider, model, unknown_chinese),
        }
