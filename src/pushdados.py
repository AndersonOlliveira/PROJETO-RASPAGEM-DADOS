import os
import re
import random
import traceback

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




def upDados(self,dados_tabela):
    futures = []
    retorno_insert =[]
    contador_por_fonte = defaultdict(lambda: {
        "INSERT": 0,
        "JB": 0, #JA NA BASE
        "ERROR":0,
        "QTINSERT": 0,
        "UPDATE": 0,
        "UPDATE_NAME": 0,
    
        })
    #
    if not dados_tabela:
        return None
   
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        # with self.db.get_connection() as conn:

                # quantidade_registros = min(4, len(dados_tabela))
                # indices_aleatorios = random.sample(
                # range(len(dados_tabela)), quantidade_registros
                #             )
                
                # for indice in indices_aleatorios:
                #     registro = dados_tabela.iloc[indice]
            # processa em blocos de 100 registros
            batch_size = 100
            print(type(dados_tabela))

            dados_tabela = pd.DataFrame(dados_tabela)
            subset = dados_tabela.iloc[:206, :]

            for start in range(0, len(subset), batch_size):
                    bloco = subset.iloc[start:start + batch_size]
                    for _, registro in bloco.iterrows():
                        # print(registro)
                        print(registro['NOME'])
                        # futures.append(executor.submit(exists_by_name,conn,registro['NOME'],registro['DATA_FALECIMENTO']))
                        result_exists = executor.submit(exists_by_name,self,registro['NOME'],registro['DATA_FALECIMENTO'])

                        print(f"f result_exists {result_exists}")
                        try:
                            resultado = result_exists.result() # PEGO O RETORNO VINDO DA VERIFICAR DO REGISTRO O QUE FOR FALSE SOMENTE
                            #  print(f"Future: {future}")
                            #  print(f"Retorno do future: {resultado}")
                            #  print(f"Retorno do future: {registro}")
                            if resultado is True:
                                contador_por_fonte[registro['LINK_FONTE']]["JB"] += 1
                            elif resultado is False:
                                #   print("RESULTADO DO FUTURE: False")
                                futures.append(registro)
                        except Exception as e:
                                erro_detalhado = traceback.format_exc()
                                print(f"TENHO ERRO NESTE PONTO PARA ACESSAR O REGISTRO {erro_detalhado}")
                                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO RESULT EXISTS {str(e)}")



                

        # try:
        #     for future in as_completed(futures):
        #         resultado = future.result()
        #         print(f"Future: {future}")
        #         print(f"Retorno do future: {resultado}")
        #         print(f"Retorno do future: {registro}")

        #         if resultado is True:
        #             print("RESULTADO DO FUTURE: True")
        #         elif resultado is False:
        #             print("RESULTADO DO FUTURE: False")
        # except Exception as e:
        #     print(f"TENHO ERRO NESTE PONTO PARA ACESSAR O REGISTRO {e}")
 
    # print(f"MEU FUTURE POPULAOD {futures}")
    if futures:
        
        # PREPARAR PARA INSERIR NO BANCO DE DADOS
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                print(f"quantidade de processos {self.max_workers}")
                # with self.db.get_connection() as conn:
                for list_register in futures:
                    print(f"MINHA LISTA DE REGISTRO DO FUTURE {list_register}")
                    retorno_insert.append(
                                executor.submit(
                                insert_base_obito,self,list_register
                                )
                            )

            

        for dados_inserts in as_completed(retorno_insert):
             resultado = dados_inserts.result()
             if 'sucesso' in resultado['status']:
                 contador_por_fonte[registro['LINK_FONTE']]["INSERT"] += 1
                  
              

             print(f"RETORNO VINDO DO INSERT DO OBITO {resultado}")


    print(f"MEU CONTADOR {contador_por_fonte}")
        

 

       ## SE FOR FALSE PASSA PARA O PASSO DE INSERIR NA BASE COM OS DADOS VINDO DO ARQUIVO
  


def base_obito(self, todos_dados):

    futures = []
    falhas_ids = []
    
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:


        # with self.db.get_connection() as conn:
            dados_df = pd.DataFrame(todos_dados)
            for lista in todos_dados.itertuples(index=False):
                print(f"acessando alista aqui {lista.NOME}")
                # print(f"acesando alista aqui {lista.get('NOME')}")
                # futures.append(
                #     executor.submit(
                #        exists_by_name,conn,lista.NOME,lista.DATA_FALECIMENTO
                     
                #     )
                # )

            print(f"MEU FETURE POPULADO {futures}")

            for future in as_completed(futures):
                print('teste')
            #     resultado = future.result()
            #      # atualiza contador (thread-safe aqui no main)
            #     if resultado:
            #         sigla = resultado.get("sigla", "N/I")

            #         match resultado.get("acao"):
            #             case "INSERT":
            #                 contador_por_pais[sigla]["INSERT"] += 1

            #             case "UPDATE":
            #                 contador_por_pais[sigla]["UPDATE"] += 1

            #             case "UPDATE_NAME":
            #                 contador_por_pais[sigla]["UPDATE_NAME"] += 1

            #             case "ERROR":
            #                 falhas_ids.append(resultado['dados_error'])
            #                 contador_por_pais[sigla]["ERROR"] += 1

            #             case _:
            #                 contador_por_pais[sigla]["NA"] += 1


            # print(f"MEU CONTADOR PREENCHDIDO {contador_por_pais}")
            # ClassLogger.logger.info(f"MEU CONTADOR PREENCHDIDO {contador_por_pais}")
