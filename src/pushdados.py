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
    if not dados_tabela:
            print("Nenhum dado recebido para processamento.")
            return None
    registros_para_inserir = []
    lista_error = []
    tabela_atualizar = []

    fontes_atualizadas = set()

    contador_por_fonte = defaultdict(
        lambda: {
            "INSERT": 0,
            "JB": 0,
            "ERROR": 0,
            "QTINSERT": 0,
            "UPDATE": 0,
            "UPDATE_NAME": 0,
        }
    )
    # ------------------------------------------------------------------
    # CONVERTE PARA DATAFRAME
    # ------------------------------------------------------------------

    try:
        dados_df = pd.DataFrame(dados_tabela)
    except Exception as e:
        erro_detalhado = traceback.format_exc()

        ClassLogger.logging.error(
            "ERRO AO CONVERTER DADOS PARA DATAFRAME: %s",
            erro_detalhado
        )

        return None
    
    total = len(dados_df)

    if total == 0:
        print("DataFrame vazio.")
        return None

    print("=" * 80)
    print("INÍCIO DO PROCESSAMENTO")
    print("Total de registros:", total)
    print("Máximo de workers:", self.max_workers)
    print("Tamanho do lote:", self.process_lote)
    print("=" * 80)

    # ------------------------------------------------------------------
    # PROCESSAMENTO EM LOTES
    # ------------------------------------------------------------------

    batch_size = self.process_lote
    
   
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

        for start in range(0, total, batch_size):

            fim = min(start + batch_size, total)

            bloco = dados_df.iloc[start:fim]

            print(
                "Processando registros %s até %s de %s"
                % (start + 1, fim, total)
            )

            # ----------------------------------------------------------
            # FUTURES DE VERIFICAÇÃO
            # ----------------------------------------------------------

            futures_verificacao = {}

            for _, registro in bloco.iterrows():

                try:
                    nome = registro["NOME"]
                    data_falecimento = registro["DATA_FALECIMENTO"]

                    future = executor.submit(
                        exists_by_name,
                        self,
                        nome,
                        data_falecimento
                    )

                    # Guarda o registro correspondente ao Future
                    futures_verificacao[future] = registro

                    # --------------------------------------------------
                    # REGISTRA A FONTE
                    # --------------------------------------------------

                    fonte = registro.get("LINK_FONTE", "")

                    if fonte not in fontes_atualizadas:

                        tabela_atualizar.append(
                            {
                                "LINK_FONTE": fonte
                            }
                        )

                        fontes_atualizadas.add(fonte)

                except Exception as e:

                    erro_detalhado = traceback.format_exc()

                    print(
                        "Erro ao criar processamento para registro: %s"
                        % erro_detalhado
                    )

                    ClassLogger.logging.error(
                        "ERRO AO CRIAR FUTURE EXISTS_BY_NAME: %s",
                        erro_detalhado
                    )

                    lista_error.append(
                        {
                            "status": "ERRO_FATAL",
                            "erro": str(e),
                            "dados": registro.to_dict()
                        }
                    )

            # ----------------------------------------------------------
            # PROCESSA OS RESULTADOS DA VERIFICAÇÃO
            # ----------------------------------------------------------

            for future in as_completed(futures_verificacao):

                registro = futures_verificacao[future]

                fonte = registro.get("LINK_FONTE", "")

                try:

                    resultado = future.result()

                    print(
                        "RETORNO EXISTS_BY_NAME:",
                        resultado
                    )

                    # --------------------------------------------------
                    # ERRO DE CONEXÃO
                    # --------------------------------------------------

                    if (
                        isinstance(resultado, dict)
                        and resultado.get("status") == "erro_conexao"
                    ):

                        contador_por_fonte[fonte]["ERROR"] += 1

                        resultado["LINK_FONTE"] = fonte

                        lista_error.append(resultado)

                        ClassLogger.logging.error(
                            "ERRO DE CONEXÃO AO CONSULTAR REGISTRO: %s",
                            resultado
                        )

                        continue

                    # --------------------------------------------------
                    # DATA DE FALECIMENTO INVÁLIDA
                    # --------------------------------------------------

                    if (
                        isinstance(resultado, dict)
                        and resultado.get("status") == "data_falecimento"
                    ):

                        contador_por_fonte[fonte]["ERROR"] += 1

                        resultado["LINK_FONTE"] = fonte

                        lista_error.append(resultado)

                        ClassLogger.logging.error(
                            "DADOS NÃO FORMATADOS: %s",
                            resultado
                        )

                        continue

                    # --------------------------------------------------
                    # JÁ EXISTE NA BASE
                    # --------------------------------------------------

                    if resultado is True:

                        contador_por_fonte[fonte]["JB"] += 1

                        continue

                    # --------------------------------------------------
                    # NÃO EXISTE -> SERÁ INSERIDO
                    # --------------------------------------------------

                    if resultado is False:

                        registros_para_inserir.append(
                            registro
                        )

                        contador_por_fonte[fonte]["QTINSERT"] += 1

                        continue

                    # --------------------------------------------------
                    # RETORNO DESCONHECIDO
                    # --------------------------------------------------

                    contador_por_fonte[fonte]["ERROR"] += 1

                    lista_error.append(
                        {
                            "status": "ERRO_RETORNO_EXISTS",
                            "erro": "Retorno desconhecido de exists_by_name",
                            "LINK_FONTE": fonte,
                            "NOME": registro.get("NOME"),
                            "DATA_FALECIMENTO": registro.get(
                                "DATA_FALECIMENTO"
                            ),
                            "resultado": resultado
                        }
                    )

                    ClassLogger.logging.error(
                        "RETORNO DESCONHECIDO DO EXISTS_BY_NAME: %s",
                        resultado
                    )

                except Exception as e:

                    erro_detalhado = traceback.format_exc()

                    contador_por_fonte[fonte]["ERROR"] += 1

                    lista_error.append(
                        {
                            "status": "ERRO_EXISTS",
                            "erro": str(e),
                            "LINK_FONTE": fonte,
                            "NOME": registro.get("NOME"),
                            "DATA_FALECIMENTO": registro.get(
                                "DATA_FALECIMENTO"
                            )
                        }
                    )

                    print(
                        "ERRO AO PROCESSAR RESULTADO EXISTS:"
                    )

                    print(erro_detalhado)

                    ClassLogger.logging.error(
                        "ERRO NO PROCESSAMENTO DO EXISTS_BY_NAME: %s",
                        erro_detalhado
                    )

    # ------------------------------------------------------------------
    # INSERÇÃO DOS REGISTROS
    # ------------------------------------------------------------------

    if registros_para_inserir:

        print("=" * 80)
        print(
            "REGISTROS PARA INSERÇÃO:",
            len(registros_para_inserir)
        )
        print("=" * 80)

        futures_insert = {}

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            for registro in registros_para_inserir:

                future = executor.submit(
                    insert_base_obito,
                    self,
                    registro
                )

                futures_insert[future] = registro

            # ----------------------------------------------------------
            # PROCESSA RESULTADOS DOS INSERTS
            # ----------------------------------------------------------

            for future in as_completed(futures_insert):

                registro = futures_insert[future]

                fonte_registro = registro.get(
                    "LINK_FONTE",
                    ""
                )

                try:

                    resultado = future.result()

                    print(
                        "RETORNO INSERT:",
                        resultado
                    )

                    # --------------------------------------------------
                    # RETORNO INVÁLIDO
                    # --------------------------------------------------

                    if (
                        not resultado
                        or not isinstance(resultado, dict)
                    ):

                        contador_por_fonte[
                            fonte_registro
                        ]["ERROR"] += 1

                        lista_error.append(
                            {
                                "status": "ERRO_FATAL",
                                "erro": (
                                    "A inserção não retornou "
                                    "um resultado válido."
                                ),
                                "LINK_FONTE": fonte_registro,
                                "NOME": registro.get("NOME"),
                                "DATA_FALECIMENTO": registro.get(
                                    "DATA_FALECIMENTO"
                                ),
                                "resultado": resultado
                            }
                        )

                        ClassLogger.logging.error(
                            "INSERCAO RETORNOU RESULTADO INVALIDO: %r",
                            resultado
                        )

                        continue

                    # --------------------------------------------------
                    # FONTE DO RETORNO
                    # --------------------------------------------------

                    fonte = resultado.get(
                        "LINK_FONTE",
                        fonte_registro
                    )

                    status = str(
                        resultado.get("status", "")
                    ).lower()

                    print(
                        "STATUS INSERT:",
                        status
                    )

                    # --------------------------------------------------
                    # INSERT REALIZADO
                    # --------------------------------------------------

                    if "sucesso" in status:

                        contador_por_fonte[
                            fonte
                        ]["INSERT"] += 1

                    # --------------------------------------------------
                    # ERRO NO INSERT
                    # --------------------------------------------------

                    elif (
                        "erro" in status
                        or "ERRO_FATAL" in status.upper()
                    ):

                        contador_por_fonte[
                            fonte
                        ]["ERROR"] += 1

                        resultado["LINK_FONTE"] = fonte

                        lista_error.append(
                            resultado
                        )

                    # --------------------------------------------------
                    # RETORNO NÃO RECONHECIDO
                    # --------------------------------------------------

                    else:

                        contador_por_fonte[
                            fonte
                        ]["ERROR"] += 1

                        resultado["LINK_FONTE"] = fonte

                        lista_error.append(
                            {
                                "status": "ERRO_STATUS",
                                "erro": (
                                    "Status de inserção "
                                    "não reconhecido."
                                ),
                                "LINK_FONTE": fonte,
                                "resultado": resultado
                            }
                        )

                except Exception as e:

                    erro_detalhado = traceback.format_exc()

                    contador_por_fonte[
                        fonte_registro
                    ]["ERROR"] += 1

                    lista_error.append(
                        {
                            "status": "ERRO_INSERT",
                            "erro": str(e),
                            "LINK_FONTE": fonte_registro,
                            "NOME": registro.get("NOME"),
                            "DATA_FALECIMENTO": registro.get(
                                "DATA_FALECIMENTO"
                            )
                        }
                    )

                    print(
                        "ERRO NO INSERT:"
                    )

                    print(erro_detalhado)

                    ClassLogger.logging.error(
                        "ERRO PROCESSANDO INSERT: %s",
                        erro_detalhado
                    )

    else:

        print(
            "Nenhum registro novo para inserir."
        )

    # ------------------------------------------------------------------
    # ENVIO DOS ERROS
    # ------------------------------------------------------------------

    try:

        if lista_error:

            print("=" * 80)
            print(
                "TOTAL DE ERROS:",
                len(lista_error)
            )
            print("=" * 80)

            erros_para_enviar = list(lista_error)

            df_erros = pd.DataFrame(
                erros_para_enviar
            )

            html_tabela = df_erros.to_html(
                index=False,
                border=1,
                justify="center"
            )

            # ----------------------------------------------------------
            # SALVA CSV
            # ----------------------------------------------------------

            pasta = "arquivos/error"
            documento = "documento_erros"

            salvar_csv_error(
                erros_para_enviar,
                pasta,
                documento
            )

            # ----------------------------------------------------------
            # ENVIA E-MAIL
            # ----------------------------------------------------------

            enviar_email_all(
                html_tabela
            )

            print(
                "E-mail de erros enviado com sucesso."
            )

            # Evita duplicidade
            lista_error.clear()

        else:

            print(
                "Nenhum erro para enviar por e-mail."
            )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "ERRO NO PROCESSAMENTO/ENVIO DOS ERROS:"
        )

        print(erro_detalhado)

        ClassLogger.logging.error(
            "ERRO PROCESSAMENTO ENVIO DE ERROS: %s",
            erro_detalhado
        )

    # ------------------------------------------------------------------
    # MONTA RESUMO POR FONTE
    # ------------------------------------------------------------------

    print("=" * 80)
    print("CONTADOR POR FONTE")
    print("=" * 80)

    print(contador_por_fonte)

    for linha in tabela_atualizar:

        fonte = linha["LINK_FONTE"]

        contador = contador_por_fonte[fonte]

        linha["QTA A INSERIR"] = contador["QTINSERT"]

        linha["QTA J/N BASE"] = contador["JB"]

        linha["QTA ERROR"] = contador["ERROR"]

        linha["QTA INSERIDO"] = contador["INSERT"]

        linha["QTA UPDATE"] = contador["UPDATE"]

        linha["QTA UPDATE NAME"] = contador["UPDATE_NAME"]

    # ------------------------------------------------------------------
    # DATAFRAME FINAL
    # ------------------------------------------------------------------

    if tabela_atualizar:

        df_da_fonte_atual = pd.DataFrame(
            tabela_atualizar
        )

        print("=" * 80)
        print("RESUMO FINAL")
        print("=" * 80)

        print(
            df_da_fonte_atual.to_string(
                index=False
            )
        )

        # --------------------------------------------------------------
        # GUARDA PARA O PROCESSAMENTO GERAL
        # --------------------------------------------------------------

        if not hasattr(
            self,
            "lista_dataframes_global"
        ):
            self.lista_dataframes_global = []

        self.lista_dataframes_global.append(
            df_da_fonte_atual
        )

    # ------------------------------------------------------------------
    # RETORNO
    # ------------------------------------------------------------------

    print("=" * 80)
    print("PROCESSAMENTO FINALIZADO")
    print("=" * 80)

    return True