import pandas as pd
from pathlib import Path
from datetime import datetime
from Mail.ClassMail import enviar_email_all
from utils.info_pastas import abrir_arquivos



class CrawlerStats:

    def __init__(self):

        self.inicio = datetime.now()
        self.todos_resultados = []

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

    def salvar(self, pasta, nome):
        fim = datetime.now()
        self.stats["servidor"] = nome
        self.stats["inicio"] = self.inicio.strftime("%d/%m/%Y %H:%M:%S")
        self.stats["fim"] = fim.strftime("%d/%m/%Y %H:%M:%S")
        self.stats["duracao_segundos"] = round((fim-self.inicio).total_seconds(),2)
        self.stats["Qta_registros"],self.stats["Qta_diferença"], self.stats["Qta_registro_anteriores"] = abrir_arquivos(pasta)

        df = pd.DataFrame([self.stats])
       
        df.to_csv(
            Path(pasta) / "estatisticas.csv",
            sep=";",
            encoding="utf-8-sig",
            index=False
        )

        self.todos_resultados.append(df)

def enviar_relatorio_email(self):

    if not self:
        print("Nenhum resultado para enviar.")
        return
        
    df_consolidado = pd.concat(self, ignore_index=False)
    convert = df_consolidado.to_html(index=False, border=1, justify='center')
    enviar_email_all(convert)
    # self.clear()