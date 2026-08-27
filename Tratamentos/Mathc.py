import os
import re
import numpy as np
import pandas as pd
import traceback
from pathlib import Path
from collections import Counter, defaultdict
from Logs import ClassLogger
from utils.auxliares import auxliares
from utils.unicode import remover,limpar_nome_rn
from datetime import time,datetime
from services.crawler import iniciar
from Model.ClassModel import full_dados, search_from_name_obito
from concurrent.futures import ThreadPoolExecutor, as_completed


def mathc_process(self):
    lista_cnt_localizado = []
    print(f"VOU PEGAR O RETORNO PARA VALIDAR OS DADOS")

    #LISTA COM O NOME E DATA DE NASCIMENTO
    retorno_nome = full_dados(self)

    if not retorno_nome:
        return None

    try:
       
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            dados_tabela = pd.DataFrame(retorno_nome)
            batch_size = self.process_lote
            total = len(dados_tabela)
            print(f"Total de registros para processar: {total}")
            for start in range(0, total, batch_size):
                bloco = dados_tabela.iloc[start:start + batch_size]
                print(f"Processando registros "f"{start + 1} até {min(start + batch_size, total)} "f"de {total}")
                for _, registro in bloco.iterrows():
                   result_exists =  executor.submit(search_from_name_obito,self,limpar_nome_rn(registro['nome']),registro['data_nascimento'],registro['obito_id'],registro)
                   lista_cnt_localizado.append(result_exists.result())
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS {str(e)}")


    print(type(result_exists))
    try:
        # resultado = result_exists.result() # PEGO O RETORNO VINDO DA VERIFICAR DO REGISTRO O QUE FOR FALSE SOMENTE
        print(f"RETORNO DO EXISTIS {lista_cnt_localizado}")
        if (isinstance(lista_cnt_localizado, dict) and lista_cnt_localizado.get('status') == 'erro_conexao'):
            print(f"Error vindo na procura dos dados {lista_cnt_localizado}")
            contador_por_fonte[registro['LINK_FONTE']]["JB"] += 1
            ClassLogger.logging.error(f"Error vindo na procura dos dados {resultado}")
                continue 
        if (isinstance(resultado, dict) and resultado.get('status') == 'data_falecimento'):
            contador_por_fonte[registro['LINK_FONTE']]["ERROR"] += 1
            lista_error.append(resultado)
            ClassLogger.logging.error(f"DADOS NÃO FORMATADO {resultado}")
                 continue
         if resultado is True:
            contador_por_fonte[registro['LINK_FONTE']]["JB"] += 1
        elif resultado is False:
            futures.append(registro)
        
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar o Exists: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO RESULT EXISTS {str(e)}")


    # for chave, valor in retorno_nome.items():
    #     print(f"{chave}: {valor}")
    # lista_cnt_localizado = []
    # for registro in retorno_nome:
    #     nome = limpar_nome_rn(registro['nome'])

    #     data_nasc = registro['data_nascimento']
    #     print(f"{nome}: {data_nasc}")
    #     #BUSCA DENTRO DO MATCH NAME 



  
