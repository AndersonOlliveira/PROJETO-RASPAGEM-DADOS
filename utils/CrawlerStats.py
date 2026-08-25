import traceback
import pandas as pd
from pathlib import Path
from Logs import ClassLogger
from datetime import datetime
from Mail.ClassMail import enviar_email_all
from utils.info_pastas import abrir_arquivos
from Model.ClassModel import update_info_fontes



class CrawlerStats:

    def __init__(self,db):
    # def __init__(self,db,lock):

        self.db = db # RECEBE A CLASSE DE CONEXAO COM O BANCO
        # self.lock = lock
        self.inicio = datetime.now()
        self.todos_resultados = []
        self.processo_id = None
        self.chave = None

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

    # def id_processo(self,idRertornado):
    #     self.stats["processo_id"] = idRertornado

    def salvar(self, pasta, nome, id_processo,chaves):
        fim = datetime.now()
        dados = self.stats.copy() # copio e vou inteirando
        dados["servidor"] = nome
        dados["id_processo"] = id_processo
        dados["chaves"] = chaves

        dados["inicio"] = self.inicio.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        dados["fim"] = fim.strftime(
            "%d/%m/%Y %H:%M:%S"
        )

        dados["duracao_segundos"] = round(
            (fim - self.inicio).total_seconds(),
            2
        )

        (
            dados["qta_registros"],
            dados["qta_diferença"],
            dados["qta_registro_anteriores"]
        ) = abrir_arquivos(pasta)

        
        df = pd.DataFrame([dados])

        df.to_csv(
            Path(pasta) / "estatisticas.csv",
            sep=";",
            encoding="utf-8-sig",
            index=False
        )

        # guarda somente o resultado deste servidor
        self.todos_resultados.append(df)

def enviar_relatorio_email(self, relatorio):

    print(f"o que vem no self DO RELATORIO? FINAL? {self}")

    if not relatorio:
        print("Nenhum resultado para enviar.")
        return None

    try:
        # Junta todos os DataFrames recebidos
        df_consolidado = pd.concat(relatorio, ignore_index=False)

        print("======================================")
        print("DATAFRAME CONSOLIDADO")
        print(df_consolidado)
        print("======================================")

        chaves_servidores = []

        # Atualiza cada processo
        for _, linha in df_consolidado.iterrows():

            processo_id = linha["id_processo"]
            qta_registros = linha["qta_registros"]
            key_servidores = linha["chaves"]

            print(f"Atualizando processo: {processo_id}")
            print(f"Quantidade de registros: {qta_registros}")
            print(f"Chaves: {key_servidores}")

            retorno_update = update_info_fontes(
                self,
                processo_id,
                qta_registros
            )

            if retorno_update:
                chaves_servidores.append(key_servidores)

        print("======================================")
        print("PROCESSAMENTO DOS UPDATES FINALIZADO")
        print(f"Chaves processadas: {chaves_servidores}")
        print("======================================")

        # Só gera o HTML depois de terminar os updates
        if not df_consolidado.empty:

            convert = df_consolidado.to_html(
                index=False,
                border=1,
                justify="center"
            )

            print(f"CHEGANDO AQUI? {type(convert)}")

           
            enviar_email_all(convert)

        else:
            print("DataFrame consolidado está vazio.")

        return chaves_servidores

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            f"Falha em acessar o consolidado. {erro_detalhado}"
        )

        ClassLogger.logging.error(
            f"Falha em acessar o consolidado: {str(e)}"
        )

        return None
    
    # self.clear()