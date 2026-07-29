import logging
from logging.handlers import RotatingFileHandler
#//*====================================================
#//*Config do log
#//*====================================================
class log:
    # classLogger.py
    # Logger 1 - Main Logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('falecidos.log'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger('falecidos')

# Logger 2 - URLs Logger
urls_logger_handler = RotatingFileHandler('info_urls/falecidos_logger_urls.log')
urls_logger_handler.setLevel(logging.INFO)
urls_logger_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger_urls = logging.getLogger('trabalho_escravo_logger_urls')
logger_urls.addHandler(urls_logger_handler)
logger_urls.addHandler(logging.StreamHandler())
logger_urls.setLevel(logging.INFO)
