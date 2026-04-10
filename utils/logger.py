import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "cli_agent",
    log_dir: str = "./logs",
    console_level: int = logging.DEBUG,
    file_level: int = logging.INFO,
) -> logging.Logger:
    """创建并返回一个配置好的logger"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
    # 设置文件日志级别
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    # 设置控制台日志级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
