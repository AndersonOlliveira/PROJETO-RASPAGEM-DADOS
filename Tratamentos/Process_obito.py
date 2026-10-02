import os
import io
import re
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from Logs import ClassLogger
from datetime import time,datetime
from services.crawler import iniciar
from utils.auxliares import auxliares
from Mail.ClassMail import enviar_email_all,enviar_email_all_anexo
from collections import Counter, defaultdict
from utils.unicode import remover,limpar_nome_rn
from utils.tratar_url import e_url_valida
from utils.data import formartar_data
from concurrent.futures import ThreadPoolExecutor, as_completed
from Model.ClassModel import get_list_cpf,get_list_cpf_cntid,get_list_cntobito,cnt_obitos_inserts,update_cntobito




def verify_cnt_obito(self):
    
    list_found = []
    lista_n_found =[]
    result_update_cntobito =[]
    result_inserts_cntobito = []
    lista_cnt_id_localizado = []
    lista_dados_obtitos_cndid = []
  
    
    contador_macth = defaultdict(lambda: {
        "FOUND": 0,
        "N_EN": 0, #JA NA BASE
        "ERROR":0,
        "QTPUSH": 0,
        "UPDATE": 0,
        "UPDATE_NAME": 0,
    })
    contador_macth_cntobito = {
        "INSERIDOS": 0,
        "ERROR": 0,
        "UPDATE": 0,
        "N_EN": 0,
        "TOTAL": 0,
        "N_ALTERAR":0
    }
    #LISTA COM O NOME E DATA DE NASCIMENTO
    retorno_list_cpf = get_list_cpf(self)

    print(f"LIST COM OS REGISTRO COM CPF VINDO DO BETA {retorno_list_cpf}")

    if not retorno_list_cpf:
        return contador_macth_cntobito, result_inserts_cntobito


    try:
           
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                dados_tabela = pd.DataFrame(retorno_list_cpf)
                batch_size = self.process_lote
                total = len(dados_tabela)
                print(f"Total de registros para processar: {total}")
                contador_macth_cntobito['TOTAL'] = total
                for start in range(0, total, batch_size):
                    bloco = dados_tabela.iloc[start:start + batch_size]
                    print(f"Processando registros "f"{start + 1} até {min(start + batch_size, total)} "f"de {total}")
                    for _, registro in bloco.iterrows():
                       print(registro)
                       result_exists =  executor.submit(get_list_cpf_cntid,self,registro['cpf'],registro['link_fonte'],registro['ano'])
                       lista_cnt_id_localizado.append(result_exists.result())
    except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar CPFS : {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS  CPFS {str(e)}")

    print(f"lista localizada {lista_cnt_id_localizado}")

    print(f"tamanho localizado? {len(lista_cnt_id_localizado)}")

    try:
        
        for result_lista_cnt in lista_cnt_id_localizado:
            if isinstance(result_lista_cnt, dict):
                    ClassLogger.logging.error(
                        f"Resultado inválido na busca: {result_lista_cnt!r}"
                    )
                    continue
            print(f"MINHA LISTA PARA PROCESSAR {result_lista_cnt}")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                dados_tabela = pd.DataFrame(result_lista_cnt)
                batch_size = self.process_lote
                total = len(dados_tabela)
                print(f"Total de registros para processar: {total}")
                for start in range(0, total, batch_size):
                    bloco = dados_tabela.iloc[start:start + batch_size]
                    print(f"Processando registros "f"{start + 1} até {min(start + batch_size, total)} "f"de {total}")
                    for _, registro in bloco.iterrows():
                        result_exists_obitos =  executor.submit(get_list_cntobito,self,registro['cpf'],registro['cntId'],registro['link'],registro['ano'])
                        lista_dados_obtitos_cndid.append(result_exists_obitos.result())

    except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar o Exists: {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO RESULT EXISTS {str(e)}")


    print(f"LISTA {lista_dados_obtitos_cndid}")
    print(f"TAAMNHAO DA LISTA.. {len(lista_dados_obtitos_cndid)}")
   
    for result_lista in lista_dados_obtitos_cndid:
        if not isinstance(result_lista, dict):
            ClassLogger.logging.error(f"Resultado inválido na busca: {result_lista!r}")
            continue
              
        if result_lista.get('status') == 'n_localizado':
            contador_macth['n_encontrado']["N_EN"] += 1
            # contador_macth_cntobito['N_EN'] += 1
            lista_n_found.append(result_lista)
            continue 
        if result_lista.get('status') == 'localizado':
            contador_macth['sucesso']["FOUND"] += 1
            list_found.append(result_lista)
          
            
        

    #LISTA COM OS DADOS NÃO ENCONTRADOS PARA INSERIR
    if  lista_n_found:
        # INSERIR NÃO LOCALIZADO
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for n_found in lista_n_found:
                    fonte_tratada = e_url_valida(n_found['fontes'])
                    ano_flecimento =  formartar_data(n_found['ano'])   
                    futuro = executor.submit(cnt_obitos_inserts, self, n_found['cntid'], fonte_tratada, n_found['ano'],ano_flecimento)
                    futures.append(futuro)
                
                for futuro in futures:
                    result_inserts_cntobito.append(futuro.result())
            
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar o CNTOBITO: {erro_detalhado}")
            ClassLogger.logging.error(f"FALHA EM INSERIR OS DOS NA CNTOBITO {str(e)}")


        contador_macth_cntobito['INSERIDOS'] = 0
        contador_macth_cntobito['ERROR'] = 0

        for result_lista in result_inserts_cntobito:
            if not isinstance(result_lista, dict):
                ClassLogger.logging.error(f"Resultado inválido na busca: {result_lista!r}")
                continue
                      
            if result_lista.get('status') == 'sucesso':
                contador_macth_cntobito['INSERIDOS'] += 1
            elif result_lista.get('status') == 'error':
                contador_macth_cntobito['ERROR'] += 1


    if list_found:
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for found in list_found:
                    registros = found.get('registros', [])
                    if isinstance(registros, dict):
                        registros = [registros]

                    for registro in registros:
                        # print(f"Registro: {registro}")
                        cntobitoflag = registro.get('cntobitoflag')
                        if cntobitoflag:
                            if cntobitoflag.upper() in auxliares.LISTA_FONTES: # ASSIM BUSCO SE EXISTIR O
                                ano_flecimento = formartar_data(found['ano'])
                                url_valida = formartar_data(found['fontes'])
                                #PREPARAR UPDATE 
                                try:
                                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                                        futures_update = []
                                        # futuro = executor.submit(update_cntobito, self, url_valida, ano_flecimento, found['ano'],found['cntid'])
                                        # futures_update.append(futuro)
                                        
                                        for futuro in futures_update:
                                            result_update_cntobito.append(futuro.result())
                                    
                                except Exception as e:
                                    erro_detalhado = traceback.format_exc()
                                    print(f"Falha ao processar update cntobito: {erro_detalhado}")
                                    ClassLogger.logging.error(f"FALHA EM PROCESSAR UPDATES {str(e)}")
                            else:
                                contador_macth_cntobito['N_ALTERAR'] += 1
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar lista  localizada: {erro_detalhado}")
            ClassLogger.logging.error(f"Falha em processar a lista localizada para atualizar : {str(e)}")



    if result_update_cntobito:
        contador_macth_cntobito['UPDATE'] = 0
        for result_lista_update in result_update_cntobito:
            if not isinstance(result_lista_update, dict):
                ClassLogger.logging.error(f"Resultado inválido na busca: {result_lista_update!r}")
                continue
                              
            if result_lista_update.get('status') == 'sucesso':
                contador_macth_cntobito['UPDATE'] += 1
            elif result_lista_update.get('status') == 'error':
                contador_macth_cntobito['ERROR'] += 1 
            elif result_lista_update.get('status') == 'falha':
                contador_macth_cntobito['ERROR'] += 1

        result_inserts_cntobito.extend(result_update_cntobito)

    
    return contador_macth_cntobito ,result_inserts_cntobito



 
 




         
    