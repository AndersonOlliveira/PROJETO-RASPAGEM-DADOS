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
from Model.ClassModel import full_dados_homonimos,search_from_name_obito,search_from_name_obito_nome,search_from_name_cidade
from Tratamentos.Mathc import process_found ,process_ano_n_bate,process_nfound





def verify_homonimos(self):
    lista_localizados = []
    lista_n_found =[]
    list_found = []
    lista_n_found =[]
    lista_homonimos =[]
    result_update_cntobito =[]
    result_inserts_cntobito = []
    lista_cnt_id_localizado = []
    lista_dados_obtitos_cndid = []
    contador_macth = defaultdict(lambda: {
           "N_EN": 0,
           "ERROR": 0, #JA NA BASE
           "FOUND":0,
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
    # print(f"VOU PEGAR O RETORNO PARA VALIDAR OS DADOS")
   
       #LISTA COM O NOME E DATA DE NASCIMENTO
    retorno_list_homonimos = full_dados_homonimos(self)
    # print(f"LIST COM OS REGISTRO COM CPF VINDO DO BETA {retorno_list_homonimos}")

    # return
    try:
           
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                dados_tabela = pd.DataFrame(retorno_list_homonimos)
                batch_size = self.process_lote
                total = len(dados_tabela)
                print(f"Total de registros para processar: {total}")
                for start in range(0, total, batch_size):
                    bloco = dados_tabela.iloc[start:start + batch_size]
                    print(f"Processando registros "f"{start + 1} até {min(start + batch_size, total)} "f"de {total}")
                    for _, registro in bloco.iterrows():
                        nasc_str = str(registro['data_nascimento']).strip()
                        if nasc_str in ['nan']:
                            result_exists =  executor.submit(search_from_name_obito,self,limpar_nome_rn(registro['nome']),None,registro['obito_id'],registro)
                            lista_localizados.append(result_exists.result())
                          
                        
                
                print(f"QUANTIDADE PARA PROCESSAR {contador_macth}")
                    #    result_exists =  executor.submit(search_from_name_obito_cidade,self,limpar_nome_rn(registro['nome']),registro['data_nascimento'],registro['obito_id'],registro)
                    #    lista_localizados.append(result_exists.result())
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS {str(e)}")


    # print(f"LIST COM OS REGISTRO COM CPF VINDO DO BETA {lista_localizados}")
    try:
        for result_lista in lista_localizados:
            if not isinstance(result_lista, dict):
                ClassLogger.logging.error(
                f"Resultado inválido na busca: {result_lista!r}"
                )
                continue
                 
            if result_lista.get('status') == 'n_encontrado':
                    # print(f"Lista com os dados não encotrado  {lista_localizados}")
                    contador_macth['n_encontrado']["N_EN"] += 1
                    lista_n_found.append(result_lista)
                       # lista_n_found.append({"obito_id": result_lista.get('id_obito')})
                    # ClassLogger.logging.error(f"Lista com os dados não encotrado  {lista_localizados}")
                    continue 
            if result_lista.get('status') == 'homonimo':
                    contador_macth['homonimo']["ERROR"] += 1
                    lista_homonimos.append(result_lista)
                    #    ClassLogger.logging.error(f"Lista com os homonimos {result_lista}")
                    continue
            if result_lista.get('status') == 'sucesso':
                    contador_macth['sucesso']["FOUND"] += 1
                    list_found.append(result_lista)
            
      
        
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"FALHA NO PROCESSAMENTO HOMONIMOS {str(e)}")

    if lista_n_found:
        print(f"AQUI VAI CAIR TODOS NÃO LOCALIZADOS\n")
        process_nfound(self,lista_n_found)

    if list_found:
        retorno_found = processa_found(self,list_found)
    if lista_homonimos:  #busco por CIDADE 
        lista_localizados_cidade_homonimos = []
        lista_process_homonimos = []
        try:
            for homonimo in lista_homonimos:
                registro = homonimo.get('registro')
                if registro is None:
                    ClassLogger.logging.error(f"Homonimo sem registro associado: {homonimo!r}")
                    continue

                partes = [parte.strip() for parte in remover(registro['cidade']).split("-")]
                cidade = partes[0]
                estado = partes[1] if len(partes) > 1 else None

                if cidade not in auxliares.INFO_CIDADE:
                    result_exists = executor.submit(search_from_name_cidade, self, limpar_nome_rn(registro['nome']), cidade, estado, registro['obito_id'], registro)
                    lista_localizados_cidade_homonimos.append(result_exists.result())
                else:
                    lista_process_homonimos.append(homonimo)
                            
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar nomes: {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS {str(e)}")

    

        lista_homonimos_cidade =[]
        lista_sucesso_cidade =[]
         # PROCESSAR LISTA DE SUCESSO LOCALIZADO SOMENTE  UM REGISTRO 
        try:
            for result_lista in lista_localizados_cidade_homonimos:
                if not isinstance(result_lista, dict):
                    ClassLogger.logging.error(f"Resultado inválido na busca: {result_lista!r}")
                    continue
              
                if result_lista.get('status') == 'homonimo':
                    contador_macth['homonimo']["ERROR"] += 1
                    lista_homonimos_cidade.append(result_lista)
                            #    ClassLogger.logging.error(f"Lista com os homonimos {result_lista}")
                    continue
                if result_lista.get('status') == 'sucesso':
                    contador_macth['sucesso']["FOUND"] += 1
                    lista_sucesso_cidade.append(result_lista)
                    
           
        
                
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar update nos nomes: {erro_detalhado}")
                ClassLogger.logging.error(f"FALHA NO PROCESSAMENTO HOMONIMOS {str(e)}")


        resultad_ = []

        if lista_localizados_cidade_homonimos:
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
                    result_dados_atualizado =  executor_found.submit(process_found,self,lista_localizados_cidade_homonimos)
                    resultad_.append(result_dados_atualizado.result())
            except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar update lista_localizados_cidade_homonimos: {erro_detalhado}")
                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS lista_localizados_cidade_homonimos {str(e)}")

        if lista_process_homonimos:
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
                    result_dados_atualizado = executor_found.submit(processa_found, self, lista_process_homonimos)
                    result_dados_atualizado.result()
             
            except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar lista_process_homonimos:: {erro_detalhado}")
                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO lista_process_homonimos {str(e)}")

def processa_found(self,list_found):
    retorno_dados = []
    list_up_n_encontrado =[]
    lista_registros_zero =[]
    lista_menor_ou_maior =[]
    
    try:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
            dados_tabela_found = pd.DataFrame(list_found)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)
            print(f"Total de registros para processar: {total_found}")
            for start in range(0, total_found, batch_size_found):
                bloco_found = dados_tabela_found.iloc[start:start + batch_size_found]
                print(f"Processando registros "f"{start + 1} até {min(start + batch_size_found, total_found)} "f"de {total_found}")
                for _, registro_bloco in bloco_found.iterrows():
                    ano_estimado = registro_bloco['registro']['ano_nascimento_estimado']
                    ano_nascimentos = registro_bloco['ano_nascimentos']
                    if pd.notna(ano_estimado) and pd.notna(ano_nascimentos):
                        try:
                            ano_estimado = int(float(ano_estimado))
                            ano_nascimentos = int(float(ano_nascimentos))
                        except (TypeError, ValueError):
                            continue
                        
                        anos_brutos = ano_nascimentos - ano_estimado
                       
                        #  COM BASE NO QUE FOI ACHAADO  ENTRE AS DATAS DA PARA ASSUMIR QUE O QUE FOR 0 BATE COM A DATA CALCULADA COM BASE A IDADE LOCALIZADO NAS FONTES
                        if anos_brutos == auxliares.DIFERENCA_ANOS:
                            lista_registros_zero.append(registro_bloco)
                        else:
                            lista_menor_ou_maior.append(registro_bloco)
                            
                            
            if lista_registros_zero:
                result_dados_atualizado =  executor_found.submit(process_found,self,lista_registros_zero)
                list_up_n_encontrado.append(result_dados_atualizado.result())

           
            for contador_heteronimo in list_up_n_encontrado:
                # process_found returns (counter, details), so use its counter.
                if isinstance(contador_heteronimo, tuple) and contador_heteronimo:
                    contador_heteronimo = contador_heteronimo[0]
                if not isinstance(contador_heteronimo, dict):
                    ClassLogger.logging.error(f"Resultado inválido na busca: {contador_heteronimo!r}")
                    continue
                
                retorno_dados.append({'heteronimo' : contador_heteronimo.get('sucesso_heteronimo')})

            if lista_menor_ou_maior:
                result_dados_atualizado =  executor_found.submit(process_ano_n_bate,self,lista_menor_ou_maior)
                list_up_n_encontrado.append(result_dados_atualizado.result())
                
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")


    
      

