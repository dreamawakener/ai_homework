import os
from dotenv import load_dotenv
from typing import Optional


class Config:
    """配置管理类"""

    def __init__(self, env_file: str = ".env"):
        """
        初始化配置

        Args:
            env_file: 环境变量文件路径
        """
        # 加载环境变量
        load_dotenv(env_file)

        # API配置
        self.api_key = self._get_required_env("OPENAI_API_KEY")
        self.base_url = self._get_required_env("OPENAI_BASE_URL")
        self.model_name = self._get_required_env("OPENAI_MODEL_NAME")

        # 可选配置
        self.max_results = int(os.getenv("MAX_RESULTS", "50"))
        self.typing_delay = float(os.getenv("TYPING_DELAY", "0.001"))

        # 验证配置
        self._validate_config()

    def _get_required_env(self, key: str) -> str:
        """获取必需的环境变量"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"环境变量 {key} 未设置或为空")
        return value

    def _validate_config(self):
        """验证配置有效性"""
        if not self.api_key.startswith(('sk-', 'sk_')):
            print("⚠️  警告: API密钥格式可能不正确")

        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("BASE_URL 必须以 http:// 或 https:// 开头")

    def get_openai_config(self) -> dict:
        """获取OpenAI客户端配置"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url
        }

    def __repr__(self):
        return f"Config(model={self.model_name}, base_url={self.base_url})"


# 全局配置实例
config = Config()


# 便捷访问函数
def get_api_key() -> str:
    return config.api_key


def get_base_url() -> str:
    return config.base_url


def get_model_name() -> str:
    return config.model_name


def get_openai_config() -> dict:
    return config.get_openai_config()