import os
import tomllib
from pathlib import Path


def load_config() -> dict:
    """加载配置，优先从环境变量读取，否则从 config.toml 文件读取"""
    
    # 尝试从 config.toml 文件加载
    config_file = Path(__file__).parent / "config.toml"
    
    if config_file.exists():
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
    else:
        raise FileNotFoundError("config.toml 文件未找到")
    
    return config
