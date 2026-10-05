import os
import io
import re
import sys
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
from Model.ClassModel import full_dados_homonimos,search_from_name_obito,search_from_name_obito_nome,search_from_name_cidade,search_from_cpf_ano_nacimento
from Tratamentos.Mathc import process_found ,process_ano_n_bate,process_nfound






def verify_homonimos(self):
    lista_localizados = []
    lista_n_found = []
    list_found = []
    lista_n_found_cidade = []
    lista_homonimos = []
    contador_macth = defaultdict(lambda: {
           "N_EN": 0,
           "ERROR": 0, #JA NA BASE
           "FOUND":0,
           "QTPUSH": 0,
           "UPDATE": 0,
           "UPDATE_NAME": 0,
    })

    contador_ano_base = {}
    contador_ano_bases = {}
    erros_ano_base = []
    
    #LISTA COM O NOME E DATA DE NASCIMENTO
    retorno_list_homonimos = full_dados_homonimos(self)

    # print(retorno_list_homonimos) 
    # return 
    # return None,None,None,None
    if retorno_list_homonimos is None:

        contador_macth_cntobito = {
            'ERROR': 0,
            'UPDATE': 0,
            'N_ALTERAR': 0,
            'FOUND': 0
        }

        return contador_macth_cntobito, []
    try:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                dados_tabela = pd.DataFrame(retorno_list_homonimos)
                batch_size = self.process_lote
                total = len(dados_tabela)
                concluidos_total = 0
                print(f"Total de registros para processar: {total}", flush=True)
                for start in range(0, total, batch_size):
                    bloco = dados_tabela.iloc[start:start + batch_size]
                    inicio_lote = start + 1
                    fim_lote = min(start + batch_size, total)
                    print(f"\nProcessando registros {inicio_lote} até {fim_lote} de {total}", flush=True)
                    futures = {}

                    for _, registro in bloco.iterrows():
                        nasc_str = str(registro['data_nascimento']).strip()
                        print(f"[INICIO] DE TUDO : {registro['nome']} | obito_id={registro['obito_id']} | data={registro['data_nascimento']}", flush=True)

                        if nasc_str in ['nan'] or nasc_str == 'None' or nasc_str == 'NaT':
                            print(f"[INICIO] IN NAN OR NONE {registro['nome']} | obito_id={registro['obito_id']} | sem data", flush=True)
                            result_exists = executor.submit(search_from_name_obito, self, limpar_nome_rn(registro['nome']), None, registro['obito_id'], registro)
                        else:
                            print(f"[INICIO] {registro['nome']} | obito_id={registro['obito_id']} | data={registro['data_nascimento']}", flush=True)
                            result_exists = executor.submit(search_from_name_obito, self, limpar_nome_rn(registro['nome']), str(registro['data_nascimento']), registro['obito_id'], registro)

                        futures[result_exists] = registro['obito_id']

                    concluidos_lote = 0
                    total_lote = len(futures)
                    for result_exists in as_completed(futures):
                        obito_id = futures[result_exists]
                        try:
                            resultado = result_exists.result()
                            lista_localizados.append(resultado)
                            concluidos_lote += 1
                            concluidos_total += 1
                            print(f"[OK] {concluidos_lote}/{total_lote} | total {concluidos_total}/{total} | obito_id={obito_id}", flush=True)
                        except Exception as e:
                            concluidos_lote += 1
                            concluidos_total += 1
                            print(f"[ERRO] {concluidos_lote}/{total_lote} | total {concluidos_total}/{total} | obito_id={obito_id} | {e}", flush=True)
                            ClassLogger.logging.error(f"Erro no obito_id {obito_id}:\n{traceback.format_exc()}")
    
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar nomes: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS {str(e)}")

    print(f"QTA {len(lista_localizados)} hom", flush=True)

    # return
    try:
        for result_lista in lista_localizados:
            if not isinstance(result_lista, dict):
                ClassLogger.logging.error(
                f"Resultado inválido na busca: {result_lista!r}")
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
        tb = traceback.extract_tb(e.__traceback__)
        # Pega a última linha do rastreio
        linha = tb[-1].lineno
        print(f'Ocorreu um erro na linha {linha}')



    print(f"LISTA SUCESSO QTA {len(list_found)}\n", flush=True)
    print(f"LISTA HOMINIMOS QTA {len(lista_homonimos)}\n", flush=True)
    print(f"LISTA NÃO ENCONTRADO QTA {len(lista_n_found)}\n", flush=True)

    # return None,None,None,None


    if  lista_n_found:
        # CAI NESTE PROCESSO ELE JÁ ENVIA UM EMAIL COM OS NÃO ENCONTRADOS!
        retorno_nfound =  process_nfound(self,lista_n_found)
       

    if  list_found:
        contador_ano_base, erros_ano_base = processa_found(self,list_found)
        print(f"ESTOU SAINDO PARA A LISTA DE CONTADOR PRIMEEIROSSS >>>>> {contador_ano_base} >>>>> LISTA FOUND {list_found}")
        print(f"ESTOU SAINDO PARA A LISTA DE LISTA COM ERROS PRIMEEIROSSS >>>>>> {contador_ano_base}")

    if lista_homonimos:  #busco por CIDADE 
        print(f"LISTA COM OS HOMONIMOS")
        print(lista_homonimos)
        lista_localizados_cidade_homonimos = []
        lista_process_homonimos = []
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for homonimo in lista_homonimos:
                    registro = homonimo.get('registro')
                    if registro is None:
                        ClassLogger.logging.error(f"Homonimo sem registro associado: {homonimo!r}")
                        continue

                    partes = [parte.strip() for parte in remover(registro['cidade']).split("-")]
                    cidade = partes[0]
                    estado = partes[1] if len(partes) > 1 else None

                    if cidade not in auxliares.INFO_CIDADE:
                        print(f"[CIDADE] Processando {registro['nome']} | cidade={cidade} | estado={estado} | obito_id={registro['obito_id']}", flush=True)
                        result_exists = executor.submit(search_from_name_cidade, self, limpar_nome_rn(registro['nome']), cidade, estado, registro['obito_id'], registro)
                        futures[result_exists] = registro['obito_id']
                    else:
                        lista_process_homonimos.append(homonimo)

                concluidos_lote = 0
                total_lote = len(futures)
                for result_exists in as_completed(futures):
                    obito_id = futures[result_exists]
                    try:
                        lista_localizados_cidade_homonimos.append(result_exists.result())
                        concluidos_lote += 1
                        print(f"[CIDADE OK] {concluidos_lote}/{total_lote} | obito_id={obito_id}", flush=True)
                    except Exception as e:
                        concluidos_lote += 1
                        print(f"[CIDADE ERRO] {concluidos_lote}/{total_lote} | obito_id={obito_id} | {e}", flush=True)
                        ClassLogger.logging.error(f"Erro search_from_name_cidade obito_id={obito_id}:\n{traceback.format_exc()}")
                            
        except Exception as e:
            erro_detalhado = traceback.format_exc()
            print(f"Falha ao processar LISTA HOMONIMOS DO SEARCH FROM NAME CIDADE: {erro_detalhado}")
            ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS search_from_name_cidade {str(e)}")
            tb = traceback.extract_tb(e.__traceback__)
            # Pega a última linha do rastreio
            linha = tb[-1].lineno
            print(f'Ocorreu um erro na linha {linha}')
        

   
    

        lista_homonimos_cidade =[]
        lista_sucesso_cidade =[]
         # PROCESSAR LISTA DE SUCESSO LOCALIZADO SOMENTE  UM REGISTRO 

      
        try:
            for result_lista in lista_localizados_cidade_homonimos:
                if not isinstance(result_lista, dict):
                    ClassLogger.logging.error(f"Resultado inválido na busca: {result_lista!r}")
                    continue
                if result_lista.get('status') == 'n_encontrado':
                    contador_macth['n_encontrado']["N_EN"] += 1
                    lista_n_found_cidade.append(result_lista)
                if result_lista.get('status') == 'homonimo':
                    contador_macth['homonimo']["ERROR"] += 1
                    lista_homonimos_cidade.append(result_lista)
                    continue
                if result_lista.get('status') == 'sucesso':
                    contador_macth['sucesso']["FOUND"] += 1
                    lista_sucesso_cidade.append(result_lista)
               
        
        except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar update nos nomes: {erro_detalhado}")
                ClassLogger.logging.error(f"FALHA NO PROCESSAMENTO HOMONIMOS {str(e)}")


        resultad_ = []

        if lista_n_found_cidade:
            # CAI NESTE PROCESSO ELE JÁ ENVIA UM EMAIL COM OS NÃO ENCONTRADOS!
            retorno_nfound =  process_nfound(self,lista_n_found_cidade)

        if lista_sucesso_cidade:
        # if lista_localizados_cidade_homonimos and lista_localizados_cidade_homonimos.get('status') == 'sucesso':
            # print(f"LISTA LOCALIZADO CIDADE HOMONIMOS : {lista_localizados_cidade_homonimos}")
            try:
                print(f"ESTOU ACESSANDO O process_found PARA LISTA LOCALIZADOS CIDADE HOMONIMOS", flush=True)
                print(f"LISTA DA CIDADE HOMONIMOS {lista_localizados_cidade_homonimos}", flush=True)
                result_dados_atualizado = process_found(self, lista_localizados_cidade_homonimos)
                resultad_.append(result_dados_atualizado)
                
            except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar update lista_localizados_cidade_homonimos: {erro_detalhado}")
                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS lista_localizados_cidade_homonimos {str(e)}")
        print(f"LISTA COM OS RESULTADOS ? {resultad_}")
        if lista_process_homonimos:
            try:
                print(f"ESTOU ACESSANDO O process_found PARA LISTA LOCALIZADOS HOMONIMOS {lista_process_homonimos}", flush=True)
                contador_ano_bases, erros_ano_base = processa_found(self, lista_process_homonimos)
                print(f"ESTOU SAINDO PARA A LISTA DE CONTADOR >>>>> {contador_ano_bases} >>>>> processa_found >>>>>>> {list_found}", flush=True)
                print(f"ESTOU SAINDO PARA A LISTA DE LISTA COM ERROS>>>>>> {erros_ano_base}", flush=True)

              
                    
             
            except Exception as e:
                erro_detalhado = traceback.format_exc()
                print(f"Falha ao processar lista_process_homonimos:: {erro_detalhado}")
                ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO lista_process_homonimos {str(e)}")

   # ==========================================================
    # CONSOLIDAÇÃO FINAL DOS CONTADORES
    # ==========================================================

    contador_macth_cntobito = {
        'ERROR': 0,
        'UPDATE': 0,
        'N_ALTERAR': 0,
        'FOUND': 0
    }

    lista_erros_final = []

    # ----------------------------------------------------------
    # Resultado do processamento dos encontrados
    # ----------------------------------------------------------
    if 'contador_ano_base' in locals() and contador_ano_base:

        sucesso_heteronimo = contador_ano_base.get(
            'sucesso_heteronimo',
            {}
        )

        contador_macth_cntobito['UPDATE'] += sucesso_heteronimo.get(
            'ATUALIZADO',
            0
        )

        contador_macth_cntobito['N_ALTERAR'] += sucesso_heteronimo.get(
            'N_ENCOTRATO',
            0
        )

        contador_macth_cntobito['ERROR'] += sucesso_heteronimo.get(
            'ERROR_ATUALIZAR',
            0
        )

    # ----------------------------------------------------------
    # Resultado do processamento dos homônimos por cidade/ano
    # ----------------------------------------------------------
    if 'contador_ano_bases' in locals() and contador_ano_bases:

        sucesso_heteronimo = contador_ano_bases.get(
            'sucesso_heteronimo',
            {}
        )

        contador_macth_cntobito['UPDATE'] += sucesso_heteronimo.get(
            'ATUALIZADO',
            0
        )

        contador_macth_cntobito['N_ALTERAR'] += sucesso_heteronimo.get(
            'N_ENCOTRATO',
            0
        )

        contador_macth_cntobito['ERROR'] += sucesso_heteronimo.get(
            'ERROR_ATUALIZAR',
            0
        )

    # ----------------------------------------------------------
    # Quantidade encontrada
    # ----------------------------------------------------------
    contador_macth_cntobito['FOUND'] = (
        contador_macth_cntobito['UPDATE']
        + contador_macth_cntobito['N_ALTERAR']
    )

    # ----------------------------------------------------------
    # Erros retornados pelos processos
    # ----------------------------------------------------------
    if 'erros_ano_base' in locals() and erros_ano_base:
        lista_erros_final.extend(erros_ano_base)

    print(
        "ESTOU SAINDO DA VERIFY_HOMONIMOS >>>>> {}".format(
            contador_macth_cntobito
        ),
        flush=True
    )

    print(
        "ERROS FINAIS HOMONIMOS >>>>> {}".format(
            lista_erros_final
        ),
        flush=True
    )

    return contador_macth_cntobito, lista_erros_final

def processa_found(self,list_found):
    retorno_dados = []
    list_up_n_encontrado =[]
    lista_registros_zero =[]
    lista_menor_ou_maior =[]
    contador_ano_base = {}
    erros_ano_base = []
    update_ob_localizado = []
    contador_ = defaultdict(lambda: {
               "ATUALIZADO": 0,
               "N_ENCOTRATO": 0, #JA NA BASE
               "ERROR_ATUALIZAR":0
    })
    print("ESTOU ACESSANDO O processa_found")
    # print(f"ESTOU ACESSANDO O processa_found {list_found}")
    
    # return
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
                            print(f"LISTA DOS REGISTROS {registro_bloco['registro']['nome']} ANO NASCIMENTO ESTIMADO {ano_estimado} ANO NASCIMENTO LOCALIZADO {ano_nascimentos} DIFERENCA DE ANOS {anos_brutos}")
                            dados_cpf =  search_from_cpf_ano_nacimento(self,limpar_nome_rn(registro_bloco['registro']['nome']), str(ano_nascimentos), registro_bloco['registro']['obito_id'], registro_bloco)
                            print(f"LISTA COM O RESULTADO DA BUSCA POR ANO {dados_cpf}" )

                            if dados_cpf.get('status') == 'sucesso':
                                novo_cpf = dados_cpf.get('CPF')
                                lista_registros_zero.append({'CPF':novo_cpf, 'id_obito': registro_bloco['registro']['obito_id'], 'nome': registro_bloco['registro']['nome']})
                            else:
                                lista_menor_ou_maior.append(registro_bloco)

                            # print(f"NOVO CPF LOCALIZADO {novo_cpf} PARA O REGISTRO {registro_bloco['registro']['nome']} ANO NASCIMENTO ESTIMADO {ano_estimado} ANO NASCIMENTO LOCALIZADO {ano_nascimentos} DIFERENCA DE ANOS {anos_brutos} registro?? {registro_bloco['registro']['obito_id']} ")
                            
                            # if 'CPF' in registro_bloco['registro'] and isinstance(registro_bloco['registro']['CPF'], list):
                            #     if isinstance(novo_cpf, list):
                            #         registro_bloco['registro']['CPF'].extend(novo_cpf)
                            #     elif novo_cpf:
                            #         registro_bloco['registro']['CPF'].append(novo_cpf)
                            # else:
                            #     registro_bloco['registro']['CPF'] = [novo_cpf] if isinstance(novo_cpf, str) else list(novo_cpf)
                            
                          
                        else:
                            lista_menor_ou_maior.append(registro_bloco)
                    else:
                        # print(f"REGISTRO COM ANO NASCIMENTO ESTIMADO OU ANO NASCIMENTO LOCALIZADO NULO {registro_bloco['registro']['nome']} ANO NASCIMENTO ESTIMADO {ano_estimado} ANO NASCIMENTO LOCALIZADO {ano_nascimentos}")
                        lista_menor_ou_maior.append(registro_bloco)
                       
                            
                            
            if lista_registros_zero:
                print(f"PASSANDO NO VALOR ZERO????")
                print(f"LISTA COM OS REGISTROS QUE TEM DIFERENCA DE ANOS ZERO {lista_registros_zero}")
                
            
                list_up_n_encontrado.append(process_found(self, lista_registros_zero))

           
            for contador_heteronimo in list_up_n_encontrado:
                # process_found returns (counter, details), so use its counter.
                if isinstance(contador_heteronimo, tuple) and contador_heteronimo:
                    contador_heteronimo = contador_heteronimo[0]
                if not isinstance(contador_heteronimo, dict):
                    ClassLogger.logging.error(f"Resultado inválido na busca: {contador_heteronimo!r}")
                    continue
                
                retorno_dados.append({'heteronimo' : contador_heteronimo.get('sucesso_heteronimo')})

            if lista_menor_ou_maior:
                print(f"LISTA COM OS REGISTROS QUE TEM DIFERENCA DE ANOS MAIOR OU MENOR {lista_menor_ou_maior}")
                contador_ano_base, erros_ano_base = process_ano_n_bate(
                    self, lista_menor_ou_maior
                )


    


        return contador_ano_base, erros_ano_base
        

                
    except Exception as e:
        erro_detalhado = traceback.format_exc()
        print(f"Falha ao processar update nos processa_found: {erro_detalhado}")
        ClassLogger.logging.error(f"ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF processa_found {str(e)}")


    
      

