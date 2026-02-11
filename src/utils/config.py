import tomllib
from pathlib import Path


def load_config() -> dict:
    config_file = Path(__file__).parent / "config.toml"

    if not config_file.exists():
        raise FileNotFoundError(f"配置文件 {config_file} 不存在")
    
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
        return config