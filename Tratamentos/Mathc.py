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
from concurrent.futures import ThreadPoolExecutor, as_completed
from Model.ClassModel import full_dados, search_from_name_obito, push_cpf_obito



def mathc_process(self):
    info_tipo_ = 1 #heterônimo
    info_tipo = 2 #homônimo
    retorno_dados =[]
    list_found = []
    lista_n_found =[]
    lista_homonimos =[]
    lista_cnt_localizado = []
    contador_macth = defaultdict(lambda: {
        "FOUND": 0,
        "N_EN": 0, #JA NA BASE
        "ERROR":0,
        "QTPUSH": 0,
        "UPDATE": 0,
        "UPDATE_NAME": 0,
    })
    
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


  
    try:
        # print(f"RETORNO DO EXISTIS {lista_cnt_localizado}")
        for result_lista in lista_cnt_localizado:
            if not isinstance(result_lista, dict):
                ClassLogger.logging.error(
                    f"Resultado inválido na busca: {result_lista!r}"
                )
                continue
          
            if result_lista.get('status') == 'n_encontrado':
                print(f"Lista com os dados não encotrado  {lista_cnt_localizado}")
                contador_macth['n_encontrado']["N_EN"] += 1
                lista_n_found.append(result_lista)
                # lista_n_found.append({"obito_id": result_lista.get('id_obito')})
                ClassLogger.logging.error(f"Lista com os dados não encotrado  {lista_cnt_localizado}")
                continue 
            if result_lista.get('status') == 'homonimo':
                contador_macth['homonimo']["ERROR"] += 1
                lista_homonimos.append(result_lista)
                ClassLogger.logging.error(f"Lista com os homonimos {result_lista}")
                continue
            if result_lista.get('status') == 'sucesso':
                contador_macth['sucesso']["FOUND"] += 1
                list_found.append(result_lista)
       
        lista_error_he = []
        lista_error_ho = []

        if lista_n_found:
            #VOU PRECESSAR OS NOMES NÃO LOCALIZADO INSERI NA BASE E ENVIAR UM E-MAIL COM ANEXO
            process_nfound(self,lista_n_found)
        if lista_homonimos:

           contador_homonimos , lista_error_ho = process_homonimos(self, lista_homonimos)
           retorno_dados.append({'homonimos' : contador_homonimos.get('sucesso_homonimos')})
        # ENVIO A LISTA PARA PROCESSAR ATUALIZAR OS DADOS 
        if list_found:
            contador_heteronimo , lista_error_he  = process_found(self,list_found)
            retorno_dados.append({'heteronimo' : contador_heteronimo.get('sucesso_heteronimo')})
        
        
      
        lista_error_he.extend(lista_error_ho) 

        return retorno_dados, lista_error_he



    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar o Exists lista_cnt_localizado: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO RESULT EXISTS  lista_cnt_localizado {str(e)}")
        

def process_found(self, lista_found):
    print(f"----------------------***----------")
    # return
    list_info_update = []
    list_error = []
    update_ob_localizado = []
    contador_ = defaultdict(lambda: {
           "ATUALIZADO": 0,
           "N_ENCOTRATO": 0, #JA NA BASE
           "ERROR_ATUALIZAR":0
    })
    
    if not lista_found:
        return contador_, list_error


    dados_tabela_found = pd.DataFrame(lista_found)
    # print(f"MINHA LISTA COM OS DADOS DE ENCONTRADO {dados_tabela_found}")
    # return
    try:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
            dados_tabela_found = pd.DataFrame(lista_found)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)
            print(f"Total de registros para processar: {total_found}")
            for start in range(0, total_found, batch_size_found):
                bloco_found = dados_tabela_found.iloc[start:start + batch_size_found]
                print(f"Processando registros "f"{start + 1} até {min(start + batch_size_found, total_found)} "f"de {total_found}")
                for _, registro_bloco in bloco_found.iterrows():
                    print("LISTA PARA PROCESSAR OS DADOS APROVEITADOSS....")
                    print(f"QUE LISTA EU TENHO {registro_bloco}")
                    print(f"QUE LISTA EU TENHO {registro_bloco['CPF']}")
                    if registro_bloco['CPF'] is None or pd.isna(registro_bloco['CPF']):
                        print(f"CPF ausente para o registro: {registro_bloco}")
                        ClassLogger.logging.error(f"CPF ausente para o registro: {registro_bloco}")
                        contador_['erro_heteronimo']["ERROR_ATUALIZAR"] += 1
                        list_error.append({"obito_id": registro_bloco.get('id_obito')})
                        continue
                    result_exists =  executor_found.submit(push_cpf_obito,self,registro_bloco['CPF'],registro_bloco['id_obito'],registro_bloco,auxliares.HETERENOMIO)
                    list_info_update.append(result_exists.result())
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes NO PROCESSO FOUND: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")

    try:
        if not list_info_update:
            return contador_, list_error
        
        for result_sucesso in list_info_update:
            if not isinstance(result_sucesso, dict):
                ClassLogger.logging.error(
                        f"Resultado inválido na busca: {result_sucesso!r}")
                continue
            if result_sucesso.get('status') == 'erro':
                print(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                contador_['erro_heteronimo']["ERROR_ATUALIZAR"] += 1
                list_error.append({"obito_id": result_sucesso.get('id_obito')})
                ClassLogger.logging.error(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                continue 
            if result_sucesso.get('status') == 'sucesso':
                print(f"ESTAOU SAINDO NO SUCESSO AO ATUALIZAR")
                contador_['sucesso_heteronimo']["ATUALIZADO"] += 1
                update_ob_localizado.append(result_sucesso)

        return contador_, list_error
    except Exception as e:
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")


def process_homonimos(self, l_homonimos):

    list_info_update = []
    list_error = []
    update_ob_localizado = []
    contador_ = defaultdict(lambda: {
            "ATUALIZADO": 0,
            "N_ENCOTRATO": 0, #JA NA BASE
            "ERROR_ATUALIZAR":0
               
    })
     
    if not l_homonimos:
        return contador_, list_error
     
    dados_tabela_found = pd.DataFrame(l_homonimos)
    
    try:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
            dados_tabela_found = pd.DataFrame(l_homonimos)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)
            print(f"Total de registros para processar: {total_found}")
            for start in range(0, total_found, batch_size_found):
                bloco_found = dados_tabela_found.iloc[start:start + batch_size_found]
                print(f"Processando registros "f"{start + 1} até {min(start + batch_size_found, total_found)} "f"de {total_found}")
                for _, registro_bloco in bloco_found.iterrows(): # processo feito na tabela captura obito
                        result_exists =  executor_found.submit(push_cpf_obito,self,None,registro_bloco['id_obito'],registro_bloco,auxliares.HOMONIMOS)
                        list_info_update.append(result_exists.result())
     
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")
     
    try:
        if not list_info_update:
             return contador_, list_error

             
        for result_sucesso in list_info_update:
            if not isinstance(result_sucesso, dict):
                     ClassLogger.logging.error(
                    f"Resultado inválido na busca: {result_sucesso!r}")
                     continue
            if result_sucesso.get('status') == 'erro':
                     contador_['erro_homonimos']["ERROR_ATUALIZAR"] += 1
                     list_error.append({"obito_id": result_sucesso.get('id_obito')})
                     ClassLogger.logging.error(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                     continue 
            if result_sucesso.get('status') == 'sucesso':
                    contador_['sucesso_homonimos']["ATUALIZADO"] += 1
                    update_ob_localizado.append(result_sucesso)
     
        return contador_, list_error
    
    except Exception as e:
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF list_info_update {str(e)}")

def process_nfound(self,lista_notFound):
    list_up_n_encontrado = []
    
    try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
                dados_tabela_found = pd.DataFrame(lista_notFound)
                batch_size_found = self.process_lote
                total_found = len(dados_tabela_found)
                print(f"Total de registros para processar: {total_found}")
                for start in range(0, total_found, batch_size_found):
                    bloco_found = dados_tabela_found.iloc[start:start + batch_size_found]
                    print(f"Processando registros "f"{start + 1} até {min(start + batch_size_found, total_found)} "f"de {total_found}")
                    for _, registro_bloco in bloco_found.iterrows():
                            result_exists =  executor_found.submit(push_cpf_obito,self,None,registro_bloco['id_obito'],registro_bloco,auxliares.N_ENCONTRADO)
                            list_up_n_encontrado.append(result_exists.result())
         

    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")

    dados_estruturados = []

    for item in lista_notFound:
        linha = {
            'status': item.get('status'),
            'id_obito': item.get('id_obito')
        }
        
        registro_series = item.get('registro')
        
        if hasattr(registro_series, 'to_dict'):
            dados_registro = registro_series.to_dict()
        else:
            dados_registro = registro_series
        if isinstance(dados_registro, dict):
            linha.update(dados_registro)
            
        dados_estruturados.append(linha)


    # print(f"lista atualizada  {dados_estruturados}")

    df = pd.DataFrame(dados_estruturados)

    
    corpo_html = df.to_html(index=False, border=1, justify="center")

    buffer_memoria = io.StringIO()
    df.to_csv(buffer_memoria, index=False, sep=';', encoding='utf-8-sig')
    dados_csv_bytes = buffer_memoria.getvalue().encode('utf-8-sig')
    msg = f"LISTA COM DADOS NÃO ENCONTRADO NA PROSCORE\n com a quantidade de {len(dados_estruturados)}"

    enviar_email_all_anexo(msg, dados_csv_bytes, 'relatorio_n_encontrato')

def process_ano_n_bate(self, lista_found):
    list_info_update = []
    list_error = []
    update_ob_localizado = []
    contador_ = defaultdict(lambda: {
           "ATUALIZADO": 0,
           "N_ENCOTRATO": 0, #JA NA BASE
           "ERROR_ATUALIZAR":0
    })
    print("ESTOU ACESSANDO O MATCH NAME")
    
    if not lista_found:
        return contador_, list_error

    dados_tabela_found = pd.DataFrame(lista_found)
    # print(f"MINHA LISTA COM OS DADOS DE ENCONTRADO {dados_tabela_found}")
    # return
    try:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor_found:
            dados_tabela_found = pd.DataFrame(lista_found)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)
            print(f"Total de registros para processar: {total_found}")
            for start in range(0, total_found, batch_size_found):
                bloco_found = dados_tabela_found.iloc[start:start + batch_size_found]
                print(f"Processando registros "f"{start + 1} até {min(start + batch_size_found, total_found)} "f"de {total_found}")
                for _, registro_bloco in bloco_found.iterrows():
                    result_exists =  executor_found.submit(push_cpf_obito,self,None,registro_bloco['id_obito'],registro_bloco,auxliares.ANO_N_BATE)
                    list_info_update.append(result_exists.result())

    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar process_ano_n_bate: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO process_ano_n_bate {str(e)}")

    try:
        if not list_info_update:
            return contador_, list_error
        
        for result_sucesso in list_info_update:
            if not isinstance(result_sucesso, dict):
                ClassLogger.logging.error(
                        f"Resultado inválido na busca: {result_sucesso!r}")
                continue
            if result_sucesso.get('status') == 'erro':
                contador_['erro_heteronimo']["ERROR_ATUALIZAR"] += 1
                list_error.append({"obito_id": result_sucesso.get('id_obito')})
                ClassLogger.logging.error(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                continue 
            if result_sucesso.get('status') == 'sucesso':
                contador_['sucesso_heteronimo']["ATUALIZADO"] += 1
                update_ob_localizado.append(result_sucesso)

        return contador_, list_error
    except Exception as e:
            print(f"Falha ao processar list_info_update::: {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO list_info_update::: {str(e)}")


 
