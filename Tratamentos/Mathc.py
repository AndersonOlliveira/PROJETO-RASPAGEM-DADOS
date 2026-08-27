import os
import re
import numpy as np
import pandas as pd

from pathlib import Path
from collections import Counter, defaultdict
from Logs import ClassLogger
from utils.auxliares import auxliares
from utils.unicode import remover
from datetime import time,datetime
from services.crawler import iniciar
from Model.ClassModel import insert_base_obito,exists_by_name
from concurrent.futures import ThreadPoolExecutor, as_completed


def mathc_process():
    print(f"CHAMADA PARA ENVIDO E CONSULMO DAS INFORMAÇÕES")
    
