"""
Logging Framework

统一的日志输出模块
"""

import logging
import sys
from pathlib import Path


class Logger:
    """日志管理器"""

    def __init__(self, name='pdfsc', level='INFO', log_file=None, console_output=True):
        """
        初始化日志器

        Args:
            name: 日志器名称
            level: 日志级别 (DEBUG / INFO / WARNING / ERROR)
            log_file: 日志文件路径（可选）
            console_output: 是否输出到控制台
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers = []  # 清空已有handlers

        # 日志格式
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件输出
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg):
        """调试信息"""
        self.logger.debug(msg)

    def info(self, msg):
        """普通信息"""
        self.logger.info(msg)

    def warning(self, msg):
        """警告信息"""
        self.logger.warning(msg)

    def error(self, msg):
        """错误信息"""
        self.logger.error(msg)

    def critical(self, msg):
        """严重错误"""
        self.logger.critical(msg)


def create_logger(config):
    """
    根据配置创建日志器

    Args:
        config: ConfigManager实例

    Returns:
        Logger实例
    """
    level = config.get('logging.level', 'INFO')
    console_output = config.get('logging.console_output', True)
    log_file = config.get('paths.log_file')

    return Logger(
        name='pdfsc',
        level=level,
        log_file=log_file,
        console_output=console_output
    )
