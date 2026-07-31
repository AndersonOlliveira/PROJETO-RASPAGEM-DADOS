from datetime import datetime
from pathlib import Path
import pandas as pd


class CrawlerStats:

    def __init__(self):

        self.inicio = datetime.now()

        self.stats = {
            "urls_processadas": 0,
            "sucesso": 0,
            "timeout": 0,
            "http_error": 0,
            "connection_error": 0,
            "outros_erros": 0
        }

    def processada(self):
        self.stats["urls_processadas"] += 1

    def sucesso(self):
        self.stats["sucesso"] += 1

    def timeout(self):
        self.stats["timeout"] += 1

    def http_error(self):
        self.stats["http_error"] += 1

    def connection_error(self):
        self.stats["connection_error"] += 1

    def outros_erros(self):
        self.stats["outros_erros"] += 1

    def salvar(self, pasta):

        fim = datetime.now()

        self.stats["inicio"] = self.inicio.strftime("%d/%m/%Y %H:%M:%S")
        self.stats["fim"] = fim.strftime("%d/%m/%Y %H:%M:%S")
        self.stats["duracao_segundos"] = round((fim-self.inicio).total_seconds(),2)

        df = pd.DataFrame([self.stats])

        df.to_csv(
            Path(pasta) / "estatisticas.csv",
            sep=";",
            encoding="utf-8-sig",
            index=False
        )