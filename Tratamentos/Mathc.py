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
    list_found = []
    lista_homonimos =[]
    lista_n_found =[]
    lista_cnt_localizado = []
    contador_macth = defaultdict(lambda: {
        "FOUND": 0,
        "N_EN": 0, #JA NA BASE
        "ERROR":0,
        "QTPUSH": 0,
        "UPDATE": 0,
        "UPDATE_NAME": 0,
    })
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
            # elif resultado is False:
            #     futures.append(registro)
        # print(contador_macth)


        print(f"MINHA LISTA COM OS DADOS DE NÃO ENCONTRADO {len(lista_n_found)}")
        # print(f"Lista COM HOMONIMOS :: {lista_homonimos}")

        if lista_n_found:
            #VOU PRECESSAR OS NOMES NÃO LOCALIZADO INSERI NA BASE E ENVIAR UM E-MAIL COM ANEXO
            process_nfound(self,lista_n_found)
            # print(f"Lista NÃO ENCONTRADOS NA BASE PROSCORE :: {lista_n_found}")
        

        ## ENVIO A LISTA PARA PROCESSAR ATUALIZAR OS DADOS 
        # if list_found:
        #     contado , lista_error  = process_found(self,list_found)
        

        # print(f"lista com os ids não encontrados {lista_n_found}")
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



  
def process_found(self, lista_found):
    list_info_update = []
    list_error = []
    update_ob_localizado = []
    contador_ = defaultdict(lambda: {
           "SUCESS_UPDATE": 0,
           "N_EN": 0, #JA NA BASE
           "ERROR_UPDATE":0,
           "QTPUSH": 0,
          
    })
    print("ESTOU ACESSANDO O MATCH NAME")

    if not lista_found:
        return None

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
                    print("LISTA PARA PROCESSAR")
                    # print(registro_bloco)
                    result_exists =  executor_found.submit(push_cpf_obito,self,registro_bloco['CPF'],registro_bloco['id_obito'])
                    list_info_update.append(result_exists.result())

            # executor.submit(search_from_name_obito,self,limpar_nome_rn(registro['nome']),registro['data_nascimento'],registro['obito_id'],registro)
            # resultado_update =  push_cpf_obito
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")

    try:
        if not list_info_update:
            return None
        
        for result_sucesso in list_info_update:
            if not isinstance(result_sucesso, dict):
                ClassLogger.logging.error(
                        f"Resultado inválido na busca: {result_sucesso!r}")
                continue
            if result_sucesso.get('status') == 'erro':
                print(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                contador_['erro']["ERROR_UPDATE"] += 1
                list_error.append({"obito_id": result_sucesso.get('id_obito')})
                ClassLogger.logging.error(f"TENHO ERRO PARA REALIZAR O UPDATE  {list_info_update}")
                continue 
            if result_sucesso.get('status') == 'sucesso':
                print(f"ESTAOU SAINDO NO SUCESSO AO ATUALIZAR")
                contador_['sucesso']["SUCESS_UPDATE"] += 1
                update_ob_localizado.append(result_sucesso)



        return contador_, list_error
    except Exception as e:
            print(f"Falha ao processar update nos nomes: {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {str(e)}")




def process_nfound(self,lista_notFound):
    print(f"ESTOU ACESSANDO A LISTA PARA PROCESSAR O NOT FOUND NA BASE PROSCORE")

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


    print(f"lista atuaalizad  {dados_estruturados}")

    df = pd.DataFrame(dados_estruturados)

    
    corpo_html = df.to_html(index=False, border=1, justify="center")

    buffer_memoria = io.StringIO()
    df.to_csv(buffer_memoria, index=False, sep=';', encoding='utf-8-sig')
    dados_csv_bytes = buffer_memoria.getvalue().encode('utf-8-sig')
    msg = f"LISTA COM DADOS NÃO ENCONTRADO NA PROSCORE\n com a quantidade de {len(dados_estruturados)}"

    # enviar_email_all_anexo(msg, dados_csv_bytes)
 
