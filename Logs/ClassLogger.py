import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
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

# logger = logging.getLogger('info_urls/falecidos')
# caminho = 'info_urls'
# if(os.makedirs(caminho, exist_ok=True)):
#     os.chmod(caminho, 0o777)
#     print(f"Pasta verificada/criada em: {caminho}")


# # Logger 2 - URLs Logger
# urls_logger_handler = RotatingFileHandler('info_urls/falecidos_logger_urls.log')

# urls_logger_handler.setLevel(logging.INFO)
# urls_logger_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# logger_urls = logging.getLogger('falecidos_logger_urls')
# logger_urls.addHandler(urls_logger_handler)
# logger_urls.addHandler(logging.StreamHandler())
# logger_urls.setLevel(logging.INFO)
