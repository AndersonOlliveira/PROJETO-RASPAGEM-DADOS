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




def upDados(dados_tabela):
    print(dados_tabela)

# #    dados_enviado = dados_tabela.reset_index(drop=True)

#     dados_enviado = dados_tabela.reset_index(drop=True)

#     lista_dados = dados_enviado.to_dict(orient="records")

#     for registro in lista_dados:
#         print(registro["NOME"])
    

def base_obito(self, todos_dados):

    futures = []
    falhas_ids = []
    
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:


        with self.db.get_connection() as conn:
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
