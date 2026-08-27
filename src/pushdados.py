import os
import re
import random
import traceback

import numpy as np
import pandas as pd
from utils.csv import salvar_csv_error
from pathlib import Path
from collections import Counter, defaultdict
from Logs import ClassLogger
from utils.auxliares import auxliares
from utils.unicode import remover
from datetime import time,datetime
from services.crawler import iniciar

from Model.ClassModel import insert_base_obito,exists_by_name
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.CrawlerStats import enviar_relatorio_email,enviar_email_all




def upDados(self,dados_tabela):
    futures = []
    retorno_insert =[]
    lista_error =[]
    tabela_atualizar =[]

    fontes_atualizadas = set()
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
        
            batch_size = self.process_lote
            

            dados_tabela = pd.DataFrame(dados_tabela)
            # subset = dados_tabela.iloc[:50, :]
            total = len(dados_tabela)
            # total = len(subset)

            print(f"Total de registros para processar: {total}")

            for start in range(0, total, batch_size):
                    bloco = dados_tabela.iloc[start:start + batch_size]
                    print(
                        f"Processando registros "
                        f"{start + 1} até {min(start + batch_size, total)} "
                        f"de {total}"
                    )
                    for _, registro in bloco.iterrows():
                        # futures.append(executor.submit(exists_by_name,conn,registro['NOME'],registro['DATA_FALECIMENTO']))
                        result_exists = executor.submit(exists_by_name,self,registro['NOME'],registro['DATA_FALECIMENTO'])
                        
                        # ADICIONO DENTRO DA FONTE, E VERIFICO SE JÁ EXITE PARA NÃO INSERIR NOVAMENTE!
                        fonte = registro['LINK_FONTE']
                        if fonte not in fontes_atualizadas:
                            tabela_atualizar.append({'LINK_FONTE': fonte})
                            fontes_atualizadas.add(fonte)

                       
                        try:
                            resultado = result_exists.result() # PEGO O RETORNO VINDO DA VERIFICAR DO REGISTRO O QUE FOR FALSE SOMENTE
                            print(f"RETORNO DO EXISTIS {resultado}")
                            if (
                                isinstance(resultado, dict)
                                and resultado.get('status') == 'erro_conexao'
                            ):
                                print(f"Error vindo na procura dos dados {resultado}")
                                contador_por_fonte[registro['LINK_FONTE']]["JB"] += 1
                                ClassLogger.logging.error(
                                    f"Error vindo na procura dos dados {resultado}"
                                )
                                continue 
                            if (
                                isinstance(resultado, dict)
                                and resultado.get('status') == 'data_falecimento'
                            ):
                                contador_por_fonte[registro['LINK_FONTE']]["ERROR"] += 1
                                lista_error.append(resultado)
                                ClassLogger.logging.error(
                                    f"DADOS NÃO FORMATADO {resultado}"
                                )
                                continue

                            if resultado is True:
                                contador_por_fonte[registro['LINK_FONTE']]["JB"] += 1
                            elif resultado is False:
                                #   print("RESULTADO DO FUTURE: False")
                                futures.append(registro)
                        except Exception as e:
                                erro_detalhado = traceback.format_exc()
                                print(f"TENHO ERRO NESTE PONTO PARA ACESSAR O REGISTRO {erro_detalhado}")
                                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO RESULT EXISTS {str(e)}")

    # return
    if futures:
        
        # PREPARAR PARA INSERIR NO BANCO DE DADOS
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                print(f"quantidade de processos {self.max_workers}")
                # with self.db.get_connection() as conn:
                for list_register in futures:
                    # print(f"MINHA LISTA DE REGISTRO DO FUTURE {list_register}")
                    retorno_insert.append(
                                executor.submit(
                                insert_base_obito,self,list_register
                                )
                            )
                    
        for dados_inserts in as_completed(retorno_insert):
             resultado = dados_inserts.result()
             print(f"LISTA COM OS DADOS DO COMPLENT {resultado}")

             if not resultado or not isinstance(resultado, dict):
                 ClassLogger.logging.error(
                     "INSERCAO RETORNOU UM RESULTADO INVALIDO: %r", resultado
                 )
                 lista_error.append({
                     "status": "ERRO_FATAL",
                     "erro": "A inserção não retornou um resultado válido.",
                     "resultado": resultado,
                 })
                 continue

             status = str(resultado.get('status', '')).lower()
             print(f"retorno do status? {status}")
             
             if 'sucesso' in status:
                 contador_por_fonte[resultado.get('LINK_FONTE', '')]["INSERT"] += 1
             elif 'erro' in status or 'ERRO_FATAL' in status.upper():
                   contador_por_fonte[resultado.get('LINK_FONTE', '')]["ERROR"] += 1
                   lista_error.append(resultado)
            
              

            #  print(f"RETORNO VINDO DO INSERT DO OBITO {resultado}")
    try:
        if lista_error:
            erros_para_enviar = list(lista_error)
            df_erros = pd.DataFrame(erros_para_enviar)
            #  html_tabela = df_erros.to_html(index=False, classes='table table-striped')
            convert = df_erros.to_html(index=False, border=1, justify='center')
            # COM OS ERROS VOU CRIAR UM CSV PARA
            pasta = 'arquivos/error'
            documento = f'documento_erros'
            salvar_csv_error(erros_para_enviar, pasta, documento)
            enviar_email_all(convert)
            lista_error.clear()  # limpa após enviar, para não duplicar em execuções futuras
        else:
            print('NEHUM DADO A SER ENVIADO')
    except Exception as e:
         erro_detalhado = traceback.format_exc()
         print(f"Tem o erro para o processo de envio de erros:{erro_detalhado}")
         ClassLogger.logging.error(f"ERRO PROCESAMENTO ERRO {str(e)}")

    print(f"contator populado {contador_por_fonte}")
    if contador_por_fonte:
        for linha in tabela_atualizar:
            fonte = linha['LINK_FONTE']
            linha['QTA A INSERIR'] = contador_por_fonte[fonte]["INSERT"]
            linha['QTA J/N BASE'] = contador_por_fonte[fonte]["JB"]
            linha['QTA ERROR'] = contador_por_fonte[fonte]["ERROR"]
            linha['QTA INSERIDO'] = contador_por_fonte[fonte]["INSERT"]

            
        
        df_da_fonte_atual = pd.DataFrame(tabela_atualizar)
        #ADICIONO O RESULTADO TABELA, NA VARIAVEL GLOBAL PAR ENIVAR NO FINAL
        self.lista_dataframes_global.append(df_da_fonte_atual)

        #RETONRO PROCESSO GERAL
        return True


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
