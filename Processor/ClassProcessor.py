import threading
from datetime import datetime
import time
from Logs import ClassLogger
from Tratamentos.ProcessoDados import Process
# from Processar.Process_from_name import process_from_name
# from Processar.Process_verify import process_verify_status
# from Processar.Process_MatchName import process_match_name
# from Processar.Process_limite import process_limite_countrie
# from Conexao import ConectionClass, ConectionPool
from concurrent.futures import ThreadPoolExecutor, as_completed
# from db_poll import DbPool
# from Conexao.ConectionTrheaddeConectionPoll import ConectionClass as t
# from Mail.ClassMail import enviar_email_all
# from Model.ClassModel import buscar_teste, search_data_interpol
import pandas as pd
from pathlib import Path
import csv




class Processor:
    def __init__(self, max_workers: int = 10, batch_size: int = 1000):
        # self.config = ConectionClass.DbConfig()
        self.max_workers = max_workers
        self.max_workers_conn = 2
        self.batch_size = batch_size
        # self.idProcesso = idProcesso
        self.servidor = 'https://obituario.grupoangelus.com.br/g/4'
        self.servidor_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        self.batch_counter_status1 = 0
        self.batch_counter_status2 = 0
        self.batch_counter_status4 = 0
        self.qtPage = 160 # resultado na tela e apresentado somente 160 registros 
        self.indicePage = 1
        self.time_sleps = 2
        self.periodo = 'SEMANAL'
        self.true = True
        self.false =False
        self.batch_size_verify = 50
        self.lock = threading.Lock()
        # self.db = ConectionPool.DbPool(maxconn=self.max_workers)

    def executar(self):
        inicio = datetime.now()
        ClassLogger.logging.info("=" * 80)
        ClassLogger.logging.info(f"Iniciando Consulta Site - {inicio}")
        time.sleep(2)
        ClassLogger.logging.info("=" * 80)

        try:
            
            total_processados = Process(self)

            ClassLogger.logging.info(f"minha quantidade de dados processados :  {total_processados}")
          
            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()
            ClassLogger.logging.info("---" * 80)
          

        except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {str(e)}")
            error = f"Erro fatal na execução: process_api {str(e)}"
            corpo = f"""<h2 style="color:red;">Falha no processo de Captura e tratamento dos dados</h2> <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Mensagem:: {error}</p>"""
            # enviar_email_all(corpo)

        finally:
             
             ClassLogger.logging.error(f"Aplicação finalizada!")
             
 


    def executar_ciclo(self):
        self.executar()   
        

  