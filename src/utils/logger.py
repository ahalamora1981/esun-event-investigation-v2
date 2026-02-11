import sys
from pathlib import Path
from loguru import logger

def setup_logger():
    # 1. 定义日志保存路径
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app_{time:YYYY-MM-DD}.log"

    # 2. 移除默认配置（非常重要，否则会重复打印）
    logger.remove()

    # 3. 添加控制台输出 (Stdout)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        enqueue=True,  # 异步安全
    )

    # 4. 添加文件输出 (File)
    logger.add(
        str(log_file),
        rotation="00:00",          # 每天凌晨 0 点创建新文件
        retention="30 days",       # 日志保留 30 天
        compression="zip",         # 旧日志压缩成 zip
        level="DEBUG",             # 文件记录更详细的 DEBUG 信息
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8",
        enqueue=True,              # 开启异步写入，提高性能
        backtrace=True,            # 记录异常回溯
        diagnose=True,             # 记录变量值（生产环境建议设为 False 防止泄密）
    )

    return logger

# 执行初始化
my_logger = setup_logger()

# 测试代码
if __name__ == "__main__":
    my_logger.info("日志系统初始化成功！")
    my_logger.error("这是一条错误演示")
    try:
        1 / 0
    except ZeroDivisionError:
        my_logger.exception("捕捉到除零异常：")
