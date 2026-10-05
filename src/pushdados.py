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


def upDados(self, dados_tabela):

    # ==================================================================
    # VALIDAÇÃO INICIAL
    # ==================================================================

    if not dados_tabela:

        print(
            "Nenhum dado recebido para processamento."
        )

        return None

    # ==================================================================
    # ESTRUTURAS DE CONTROLE
    # ==================================================================

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

    # ==================================================================
    # DATAFRAME
    # ==================================================================

    try:

        dados_df = pd.DataFrame(
            dados_tabela
        )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        ClassLogger.logging.error(
            "ERRO AO CONVERTER DADOS PARA DATAFRAME: %s",
            erro_detalhado
        )

        return None

    total = len(dados_df)

    if total == 0:

        print(
            "DataFrame vazio."
        )

        return None

    # ==================================================================
    # CONFIGURAÇÃO
    # ==================================================================

    batch_size = self.process_lote

    max_workers_exists = self.max_workers

    # Caso não exista, utiliza self.max_workers.

    max_workers_insert = getattr(
        self,
        "max_workers_insert",
        self.max_workers
    )

    print("=" * 80)
    print("INÍCIO DO PROCESSAMENTO")
    print("=" * 80)

    print(
        "Total de registros:",
        total
    )

    print(
        "Workers EXISTS:",
        max_workers_exists
    )

    print(
        "Workers INSERT:",
        max_workers_insert
    )

    print(
        "Tamanho do lote:",
        batch_size
    )

    print("=" * 80)

  

    with ThreadPoolExecutor(
        max_workers=max_workers_exists
    ) as executor_exists, ThreadPoolExecutor(
        max_workers=max_workers_insert
    ) as executor_insert:

        # ==============================================================
        # PROCESSAMENTO DOS LOTES
        # ==============================================================

        for start in range(
            0,
            total,
            batch_size
        ):

            fim = min(
                start + batch_size,
                total
            )

            bloco = dados_df.iloc[
                start:fim
            ]

            print("=" * 80)

            print(
                "PROCESSANDO REGISTROS %s ATÉ %s DE %s"
                % (
                    start + 1,
                    fim,
                    total
                )
            )

            print("=" * 80)

            # ==========================================================
            # FUTURES DO EXISTS
            # ==========================================================

            futures_verificacao = {}

            # ==========================================================
            # FUTURES DO INSERT
            #
            # Eles serão criados aos poucos conforme o EXISTS
            # retornar False.
            # ==========================================================

            futures_insert = {}

            # ==========================================================
            # ENVIA OS EXISTS
            # ==========================================================

            for _, registro in bloco.iterrows():

                try:

                    nome = registro[
                        "NOME"
                    ]

                    data_falecimento = registro[
                        "DATA_FALECIMENTO"
                    ]

                    future = executor_exists.submit(
                        exists_by_name,
                        self,
                        nome,
                        data_falecimento
                    )

                    # Guarda qual registro pertence
                    # a este Future.

                    futures_verificacao[
                        future
                    ] = registro

                    # ==================================================
                    # REGISTRA A FONTE
                    # ==================================================

                    fonte = registro.get(
                        "LINK_FONTE",
                        ""
                    )

                    if fonte not in fontes_atualizadas:

                        tabela_atualizar.append(
                            {
                                "LINK_FONTE": fonte
                            }
                        )

                        fontes_atualizadas.add(
                            fonte
                        )

                except Exception as e:

                    erro_detalhado = traceback.format_exc()

                    print(
                        "ERRO AO CRIAR FUTURE EXISTS:"
                    )

                    print(
                        erro_detalhado
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

                    fonte = registro.get(
                        "LINK_FONTE",
                        ""
                    )

                    contador_por_fonte[
                        fonte
                    ]["ERROR"] += 1


            for future in as_completed(
                futures_verificacao
            ):

                registro = futures_verificacao[
                    future
                ]

                fonte = registro.get(
                    "LINK_FONTE",
                    ""
                )

                try:

                    resultado = future.result()

                    print(
                        "[EXISTS] Fonte=%s | Nome=%s | Resultado=%s"
                        % (
                            fonte,
                            registro.get("NOME"),
                            resultado
                        )
                    )

                    # ==================================================
                    # ERRO DE CONEXÃO
                    # ==================================================

                    if (
                        isinstance(
                            resultado,
                            dict
                        )
                        and resultado.get(
                            "status"
                        ) == "erro_conexao"
                    ):

                        contador_por_fonte[
                            fonte
                        ]["ERROR"] += 1

                        resultado[
                            "LINK_FONTE"
                        ] = fonte

                        lista_error.append(
                            resultado
                        )

                        ClassLogger.logging.error(
                            "ERRO DE CONEXÃO AO CONSULTAR REGISTRO: %s",
                            resultado
                        )

                        continue

                    # ==================================================
                    # DATA DE FALECIMENTO INVÁLIDA
                    # ==================================================

                    if (
                        isinstance(
                            resultado,
                            dict
                        )
                        and resultado.get(
                            "status"
                        ) == "data_falecimento"
                    ):

                        contador_por_fonte[
                            fonte
                        ]["ERROR"] += 1

                        resultado[
                            "LINK_FONTE"
                        ] = fonte

                        lista_error.append(
                            resultado
                        )

                        ClassLogger.logging.error(
                            "DADOS NÃO FORMATADOS: %s",
                            resultado
                        )

                        continue

                    # ==================================================
                    # JÁ EXISTE NA BASE
                    # ==================================================

                    if resultado is True:

                        contador_por_fonte[
                            fonte
                        ]["JB"] += 1

                        continue

                    # ==================================================
                    # NÃO EXISTE
                    #
                    # **************************************************
                    # AQUI O INSERT É DISPARADO IMEDIATAMENTE.
                    # **************************************************
                    # ==================================================

                    if resultado is False:

                        contador_por_fonte[
                            fonte
                        ]["QTINSERT"] += 1

                        print(
                            "[EXISTS] NÃO EXISTE -> "
                            "ENVIANDO PARA INSERT | Fonte=%s | Nome=%s"
                            % (
                                fonte,
                                registro.get("NOME")
                            )
                        )

                        # ------------------------------------------------
                        # INSERT COMEÇA AGORA
                        # ------------------------------------------------

                        future_insert = executor_insert.submit(
                            insert_base_obito,
                            self,
                            registro
                        )

                        futures_insert[
                            future_insert
                        ] = registro

                        continue

                    # ==================================================
                    # RETORNO DESCONHECIDO
                    # ==================================================

                    contador_por_fonte[
                        fonte
                    ]["ERROR"] += 1

                    lista_error.append(
                        {
                            "status": "ERRO_RETORNO_EXISTS",
                            "erro": (
                                "Retorno desconhecido "
                                "de exists_by_name"
                            ),
                            "LINK_FONTE": fonte,
                            "NOME": registro.get(
                                "NOME"
                            ),
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

                    contador_por_fonte[
                        fonte
                    ]["ERROR"] += 1

                    lista_error.append(
                        {
                            "status": "ERRO_EXISTS",
                            "erro": str(e),
                            "LINK_FONTE": fonte,
                            "NOME": registro.get(
                                "NOME"
                            ),
                            "DATA_FALECIMENTO": registro.get(
                                "DATA_FALECIMENTO"
                            )
                        }
                    )

                    print(
                        "ERRO AO PROCESSAR RESULTADO EXISTS:"
                    )

                    print(
                        erro_detalhado
                    )

                    ClassLogger.logging.error(
                        "ERRO NO PROCESSAMENTO DO EXISTS_BY_NAME: %s",
                        erro_detalhado
                    )

            # ==========================================================
            # AGORA OS INSERTS DESTE LOTE JÁ ESTÃO:
            #
            # - executando
            # - alguns podem já ter terminado
            # - outros podem estar esperando worker
            #
            # Vamos somente coletar os resultados.
            # ==========================================================

            print(
                "Quantidade de INSERTS disparados neste lote:",
                len(futures_insert)
            )

            # ==========================================================
            # PROCESSA RESULTADOS DOS INSERTS
            # ==========================================================

            for future_insert in as_completed(
                futures_insert
            ):

                registro = futures_insert[
                    future_insert
                ]

                fonte_registro = registro.get(
                    "LINK_FONTE",
                    ""
                )

                try:

                    resultado = future_insert.result()

                    print(
                        "[INSERT] Fonte=%s | Nome=%s | Resultado=%s"
                        % (
                            fonte_registro,
                            registro.get("NOME"),
                            resultado
                        )
                    )

                    # ==================================================
                    # RETORNO INVÁLIDO
                    # ==================================================

                    if (
                        not resultado
                        or not isinstance(
                            resultado,
                            dict
                        )
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
                                "NOME": registro.get(
                                    "NOME"
                                ),
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

                    # ==================================================
                    # FONTE RETORNADA PELO INSERT
                    # ==================================================

                    fonte = resultado.get(
                        "LINK_FONTE",
                        fonte_registro
                    )

                    status = str(
                        resultado.get(
                            "status",
                            ""
                        )
                    ).lower()

                    print(
                        "[INSERT] STATUS=%s | Fonte=%s"
                        % (
                            status,
                            fonte
                        )
                    )

                    # ==================================================
                    # INSERT REALIZADO COM SUCESSO
                    # ==================================================

                    if "sucesso" in status:

                        contador_por_fonte[
                            fonte
                        ]["INSERT"] += 1

                        continue

                    # ==================================================
                    # ERRO NO INSERT
                    # ==================================================

                    if (
                        "erro" in status
                        or "ERRO_FATAL" in status.upper()
                    ):

                        contador_por_fonte[
                            fonte
                        ]["ERROR"] += 1

                        resultado[
                            "LINK_FONTE"
                        ] = fonte

                        lista_error.append(
                            resultado
                        )

                        continue

                    # ==================================================
                    # STATUS NÃO RECONHECIDO
                    # ==================================================

                    contador_por_fonte[
                        fonte
                    ]["ERROR"] += 1

                    resultado[
                        "LINK_FONTE"
                    ] = fonte

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
                            "NOME": registro.get(
                                "NOME"
                            ),
                            "DATA_FALECIMENTO": registro.get(
                                "DATA_FALECIMENTO"
                            )
                        }
                    )

                    print(
                        "ERRO NO INSERT:"
                    )

                    print(
                        erro_detalhado
                    )

                    ClassLogger.logging.error(
                        "ERRO PROCESSANDO INSERT: %s",
                        erro_detalhado
                    )

            # ==========================================================
            # RESUMO DO LOTE
            # ==========================================================

            print("-" * 80)

            print(
                "LOTE FINALIZADO:",
                start + 1,
                "até",
                fim
            )

            print(
                "EXISTS processados:",
                len(futures_verificacao)
            )

            print(
                "INSERTS disparados:",
                len(futures_insert)
            )

            print("-" * 80)

    # ==================================================================
    # ENVIO DOS ERROS
    # ==================================================================

    try:

        if lista_error:

            print("=" * 80)

            print(
                "TOTAL DE ERROS:",
                len(lista_error)
            )

            print("=" * 80)

            erros_para_enviar = list(
                lista_error
            )

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

        print(
            erro_detalhado
        )

        ClassLogger.logging.error(
            "ERRO PROCESSAMENTO ENVIO DE ERROS: %s",
            erro_detalhado
        )

    # ==================================================================
    # CONTADOR POR FONTE
    # ==================================================================

    print("=" * 80)

    print(
        "CONTADOR POR FONTE"
    )

    print("=" * 80)

    print(
        contador_por_fonte
    )

    # ==================================================================
    # MONTA RESUMO POR FONTE
    # ==================================================================

    for linha in tabela_atualizar:

        fonte = linha[
            "LINK_FONTE"
        ]

        contador = contador_por_fonte[
            fonte
        ]

        linha[
            "QTA A INSERIR"
        ] = contador[
            "QTINSERT"
        ]

        linha[
            "QTA J/N BASE"
        ] = contador[
            "JB"
        ]

        linha[
            "QTA ERROR"
        ] = contador[
            "ERROR"
        ]

        linha[
            "QTA INSERIDO"
        ] = contador[
            "INSERT"
        ]

        linha[
            "QTA UPDATE"
        ] = contador[
            "UPDATE"
        ]

        linha[
            "QTA UPDATE NAME"
        ] = contador[
            "UPDATE_NAME"
        ]

    # ==================================================================
    # DATAFRAME FINAL
    # ==================================================================

    if tabela_atualizar:

        df_da_fonte_atual = pd.DataFrame(
            tabela_atualizar
        )

        print("=" * 80)

        print(
            "RESUMO FINAL"
        )

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

    # ==================================================================
    # FINAL
    # ==================================================================

    print("=" * 80)

    print(
        "PROCESSAMENTO FINALIZADO"
    )

    print("=" * 80)

    return True