import os
import logging

def setup_logger(log_file: str = "results/scraper.log") -> logging.Logger:
    """Configures the central application logger."""
    log_file = os.path.abspath(log_file)
    directory = os.path.dirname(log_file)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    logger = logging.getLogger("flight_scraper")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_file, encoding="utf-8")

        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        c_handler.setFormatter(formatter)
        f_handler.setFormatter(formatter)

        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger
