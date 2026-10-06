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
    lista_n_found = []
    result_update_cntobito = []
    result_inserts_cntobito = []
    lista_cnt_id_localizado = []
    lista_dados_obtitos_cndid = []

    contador_macth = defaultdict(lambda: {
        "FOUND": 0,
        "N_EN": 0,
        "ERROR": 0,
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
        "N_ALTERAR": 0
    }

    # ============================================================
    # 1 - BUSCAR LISTA DE CPF
    # ============================================================

    retorno_list_cpf = get_list_cpf(self)

    print(
        "LIST COM OS REGISTRO COM CPF VINDO DO BETA {}".format(
            retorno_list_cpf
        ),
        flush=True
    )

    if not retorno_list_cpf:
        return contador_macth_cntobito, result_inserts_cntobito

    # ============================================================
    # 2 - BUSCAR CNTID
    # ============================================================

    try:

        dados_tabela = pd.DataFrame(retorno_list_cpf)

        batch_size = self.process_lote
        total = len(dados_tabela)

        print(
            "Total de registros para processar: {}".format(total),
            flush=True
        )

        contador_macth_cntobito['TOTAL'] = total

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            for start in range(0, total, batch_size):

                bloco = dados_tabela.iloc[
                    start:start + batch_size
                ]

                inicio_lote = start + 1
                fim_lote = min(
                    start + batch_size,
                    total
                )

                print(
                    "\n============================================================\n"
                    "PROCESSANDO CPF\n"
                    "Registros: {} até {} de {}\n"
                    "============================================================"
                    .format(
                        inicio_lote,
                        fim_lote,
                        total
                    ),
                    flush=True
                )

                futures = {}

                # ------------------------------------------------
                # ENVIA TODAS AS TAREFAS DO LOTE
                # ------------------------------------------------

                for _, registro in bloco.iterrows():

                    try:

                        result_exists = executor.submit(
                            get_list_cpf_cntid,
                            self,
                            registro['cpf'],
                            registro['link_fonte'],
                            registro['ano']
                        )

                        futures[result_exists] = registro['cpf']

                    except Exception:

                        print(
                            "[ERRO] Falha ao criar tarefa CPF {}".format(
                                registro['cpf']
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "Erro ao criar tarefa CPF {}:\n{}".format(
                                registro['cpf'],
                                traceback.format_exc()
                            )
                        )

                # ------------------------------------------------
                # RECEBE CONFORME AS THREADS TERMINAM
                # ------------------------------------------------

                concluidos = 0
                total_lote = len(futures)

                for result_exists in as_completed(futures):

                    cpf = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        lista_cnt_id_localizado.append(
                            resultado
                        )

                        concluidos += 1

                        print(
                            "[CPF OK] {}/{} | CPF={}".format(
                                concluidos,
                                total_lote,
                                cpf
                            ),
                            flush=True
                        )

                    except Exception as e:

                        concluidos += 1

                        print(
                            "[CPF ERRO] {}/{} | CPF={} | {}".format(
                                concluidos,
                                total_lote,
                                cpf,
                                str(e)
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "Erro no processamento CPF {}:\n{}".format(
                                cpf,
                                traceback.format_exc()
                            )
                        )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar CPFS: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS CPFS {}".format(
                str(e)
            )
        )

    print(
        "lista localizada {}".format(
            lista_cnt_id_localizado
        ),
        flush=True
    )

    print(
        "tamanho localizado? {}".format(
            len(lista_cnt_id_localizado)
        ),
        flush=True
    )

    # ============================================================
    # 3 - BUSCAR CNTOBITO
    # ============================================================

    try:

        for result_lista_cnt in lista_cnt_id_localizado:

            if isinstance(result_lista_cnt, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_lista_cnt
                    )
                )

                continue

            if not result_lista_cnt:

                continue

            print(
                "MINHA LISTA PARA PROCESSAR {}".format(
                    result_lista_cnt
                ),
                flush=True
            )

            dados_tabela = pd.DataFrame(
                result_lista_cnt
            )

            batch_size = self.process_lote
            total = len(dados_tabela)

            if total == 0:
                continue

            print(
                "Total de registros para processar: {}".format(
                    total
                ),
                flush=True
            )

            with ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:

                for start in range(0, total, batch_size):

                    bloco = dados_tabela.iloc[
                        start:start + batch_size
                    ]

                    print(
                        "Processando registros {} até {} de {}"
                        .format(
                            start + 1,
                            min(start + batch_size, total),
                            total
                        ),
                        flush=True
                    )

                    futures = {}

                    # ------------------------------------------------
                    # ENVIA TODAS AS BUSCAS DO LOTE
                    # ------------------------------------------------

                    for _, registro in bloco.iterrows():

                        try:

                            result_exists_obitos = executor.submit(
                                get_list_cntobito,
                                self,
                                registro['cpf'],
                                registro['cntId'],
                                registro['link'],
                                registro['ano']
                            )

                            futures[result_exists_obitos] = (
                                registro['cpf'],
                                registro['cntId']
                            )

                        except Exception:

                            ClassLogger.logging.error(
                                "Erro ao criar tarefa CNTOBITO:\n{}".format(
                                    traceback.format_exc()
                                )
                            )

                    # ------------------------------------------------
                    # RECEBE CONFORME TERMINAM
                    # ------------------------------------------------

                    concluidos = 0
                    total_lote = len(futures)

                    for result_exists_obitos in as_completed(
                        futures
                    ):

                        cpf, cntId = futures[
                            result_exists_obitos
                        ]

                        try:

                            resultado = (
                                result_exists_obitos.result()
                            )

                            lista_dados_obtitos_cndid.append(
                                resultado
                            )

                            concluidos += 1

                            print(
                                "[CNTOBITO OK] {}/{} | CPF={} | CNTID={}"
                                .format(
                                    concluidos,
                                    total_lote,
                                    cpf,
                                    cntId
                                ),
                                flush=True
                            )

                        except Exception as e:

                            concluidos += 1

                            print(
                                "[CNTOBITO ERRO] {}/{} | CPF={} | CNTID={} | {}"
                                .format(
                                    concluidos,
                                    total_lote,
                                    cpf,
                                    cntId,
                                    str(e)
                                ),
                                flush=True
                            )

                            ClassLogger.logging.error(
                                "Erro CNTOBITO CPF={} CNTID={}:\n{}".format(
                                    cpf,
                                    cntId,
                                    traceback.format_exc()
                                )
                            )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar o Exists: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO RESULT EXISTS {}".format(
                str(e)
            )
        )

    print(
        "LISTA {}".format(
            lista_dados_obtitos_cndid
        ),
        flush=True
    )

    print(
        "TAAMNHAO DA LISTA.. {}".format(
            len(lista_dados_obtitos_cndid)
        ),
        flush=True
    )

    # ============================================================
    # 4 - SEPARAR LOCALIZADOS / NÃO LOCALIZADOS
    # ============================================================

    for result_lista in lista_dados_obtitos_cndid:

        if not isinstance(result_lista, dict):

            ClassLogger.logging.error(
                "Resultado inválido na busca: {!r}".format(
                    result_lista
                )
            )

            continue

        if result_lista.get('status') == 'n_localizado':

            contador_macth['n_encontrado']["N_EN"] += 1

            lista_n_found.append(
                result_lista
            )

            continue

        if result_lista.get('status') == 'localizado':

            contador_macth['sucesso']["FOUND"] += 1

            list_found.append(
                result_lista
            )

    # ============================================================
    # 5 - INSERIR NÃO LOCALIZADOS
    # ============================================================

    if lista_n_found:

        try:

            with ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:

                futures = {}

                for n_found in lista_n_found:

                    try:

                        fonte_tratada = e_url_valida(
                            n_found['fontes']
                        )

                        ano_flecimento = formartar_data(
                            n_found['ano']
                        )

                        futuro = executor.submit(
                            cnt_obitos_inserts,
                            self,
                            n_found['cntid'],
                            fonte_tratada,
                            n_found['ano'],
                            ano_flecimento
                        )

                        futures[futuro] = n_found['cntid']

                    except Exception:

                        ClassLogger.logging.error(
                            "Erro ao criar INSERT CNTOBITO:\n{}".format(
                                traceback.format_exc()
                            )
                        )

                concluidos = 0
                total_lote = len(futures)

                for futuro in as_completed(futures):

                    cntid = futures[futuro]

                    try:

                        resultado = futuro.result()

                        result_inserts_cntobito.append(
                            resultado
                        )

                        concluidos += 1

                        print(
                            "[INSERT OK] {}/{} | CNTID={}"
                            .format(
                                concluidos,
                                total_lote,
                                cntid
                            ),
                            flush=True
                        )

                    except Exception as e:

                        concluidos += 1

                        print(
                            "[INSERT ERRO] {}/{} | CNTID={} | {}"
                            .format(
                                concluidos,
                                total_lote,
                                cntid,
                                str(e)
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "Erro INSERT CNTID={}:\n{}".format(
                                cntid,
                                traceback.format_exc()
                            )
                        )

        except Exception as e:

            erro_detalhado = traceback.format_exc()

            print(
                "Falha ao processar o CNTOBITO: {}".format(
                    erro_detalhado
                ),
                flush=True
            )

            ClassLogger.logging.error(
                "FALHA EM INSERIR OS DADOS NA CNTOBITO {}".format(
                    str(e)
                )
            )

        contador_macth_cntobito['INSERIDOS'] = 0
        contador_macth_cntobito['ERROR'] = 0

        for result_lista in result_inserts_cntobito:

            if not isinstance(result_lista, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_lista
                    )
                )

                continue

            if result_lista.get('status') == 'sucesso':

                contador_macth_cntobito[
                    'INSERIDOS'
                ] += 1

            elif result_lista.get('status') == 'error':

                contador_macth_cntobito[
                    'ERROR'
                ] += 1

    # ============================================================
    # 6 - PROCESSAR LOCALIZADOS
    # ============================================================

    if list_found:

        try:

            with ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:

                futures = []

                for found in list_found:

                    registros = found.get(
                        'registros',
                        []
                    )

                    if isinstance(registros, dict):

                        registros = [
                            registros
                        ]

                    for registro in registros:

                        cntobitoflag = registro.get(
                            'cntobitoflag'
                        )

                        if cntobitoflag:

                            if (
                                cntobitoflag.upper()
                                in auxliares.LISTA_FONTES
                            ):

                                ano_flecimento = formartar_data(
                                    found['ano']
                                )

                                url_valida = formartar_data(
                                    found['fontes']
                                )

                                try:

                                    futuro = executor.submit(
                                        update_cntobito,
                                        self,
                                        url_valida,
                                        ano_flecimento,
                                        found['ano'],
                                        found['cntid']
                                    )

                                    futures.append(
                                        futuro
                                    )

                                except Exception as e:

                                    print(
                                        "Falha ao criar update cntobito: {}".format(
                                            str(e)
                                        ),
                                        flush=True
                                    )

                                    ClassLogger.logging.error(
                                        "FALHA AO CRIAR UPDATE:\n{}".format(
                                            traceback.format_exc()
                                        )
                                    )

                            else:

                                contador_macth_cntobito[
                                    'N_ALTERAR'
                                ] += 1

                        else:

                            contador_macth_cntobito[
                                'N_ALTERAR'
                            ] += 1

                # ------------------------------------------------
                # RECEBE UPDATES CONFORME TERMINAM
                # ------------------------------------------------

                for futuro in as_completed(futures):

                    try:

                        resultado = futuro.result()

                        result_update_cntobito.append(
                            resultado
                        )

                    except Exception as e:

                        print(
                            "Falha ao executar update cntobito: {}".format(
                                str(e)
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "FALHA EM PROCESSAR UPDATE:\n{}".format(
                                traceback.format_exc()
                            )
                        )

        except Exception as e:

            erro_detalhado = traceback.format_exc()

            print(
                "Falha ao processar lista localizada: {}".format(
                    erro_detalhado
                ),
                flush=True
            )

            ClassLogger.logging.error(
                "Falha em processar a lista localizada para atualizar: {}".format(
                    str(e)
                )
            )

    # ============================================================
    # 7 - CONTABILIZAR UPDATES
    # ============================================================

    if result_update_cntobito:

        contador_macth_cntobito['UPDATE'] = 0

        for result_lista_update in result_update_cntobito:

            if not isinstance(
                result_lista_update,
                dict
            ):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_lista_update
                    )
                )

                continue

            if result_lista_update.get(
                'status'
            ) == 'sucesso':

                contador_macth_cntobito[
                    'UPDATE'
                ] += 1

            elif result_lista_update.get(
                'status'
            ) == 'error':

                contador_macth_cntobito[
                    'ERROR'
                ] += 1

            elif result_lista_update.get(
                'status'
            ) == 'falha':

                contador_macth_cntobito[
                    'ERROR'
                ] += 1

        result_inserts_cntobito.extend(
            result_update_cntobito
        )

    # ============================================================
    # FINAL
    # ============================================================

    print(
        "\n============================================================\n"
        "PROCESSAMENTO FINALIZADO\n"
        "============================================================\n"
        "TOTAL:      {}\n"
        "INSERIDOS:  {}\n"
        "UPDATES:    {}\n"
        "ERROS:      {}\n"
        "N_ALTERAR:  {}\n"
        "============================================================"
        .format(
            contador_macth_cntobito['TOTAL'],
            contador_macth_cntobito['INSERIDOS'],
            contador_macth_cntobito['UPDATE'],
            contador_macth_cntobito['ERROR'],
            contador_macth_cntobito['N_ALTERAR']
        ),
        flush=True
    )

    return (
        contador_macth_cntobito,
        result_inserts_cntobito
    )