import logging
import sys

def setup_logger():
    # Create logger
    logger = logging.getLogger("docmind_sys")
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Create console handler and set level to INFO
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)

    return logger

logger = setup_logger()
