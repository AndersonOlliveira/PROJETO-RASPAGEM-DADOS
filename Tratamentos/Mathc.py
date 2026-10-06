import os
import io
import re
import traceback
import threading
import faulthandler
import time as time_module

import numpy as np
import pandas as pd

from pathlib import Path
from Logs import ClassLogger
from datetime import time, datetime
from services.crawler import iniciar
from utils.auxliares import auxliares
from Mail.ClassMail import enviar_email_all, enviar_email_all_anexo
from collections import Counter, defaultdict
from utils.unicode import remover, limpar_nome_rn
from concurrent.futures import ThreadPoolExecutor, as_completed
from Model.ClassModel import full_dados, search_from_name_obito, push_cpf_obito


# ---------------------------------------------------------
# MONITORAMENTO DAS THREADS
# ---------------------------------------------------------

def _monitorar_progresso(total, concluidos, ultimo_progresso, nome_processo,
                         lock, intervalo=10):
    """
    Mostra o andamento do lote sem interferir no processamento.
    """
    while True:
        time_module.sleep(intervalo)

        with lock:
            atual = concluidos[0]
            ultimo = ultimo_progresso[0]

        if atual >= total:
            break

        tempo_sem_progresso = time_module.time() - ultimo
        percentual = (atual / float(total)) * 100 if total else 100

        print(
            "\n"
            "============================================================\n"
            "[MONITOR] {}\n"
            "Total: {}\n"
            "Concluídos: {}\n"
            "Pendentes: {}\n"
            "Percentual: {:.2f}%\n"
            "Sem progresso há: {:.0f}s\n"
            "============================================================"
            .format(
                nome_processo,
                total,
                atual,
                total - atual,
                percentual,
                tempo_sem_progresso
            ),
            flush=True
        )

        # Se nenhuma tarefa terminou durante este período, mostramos
        # a pilha de todas as threads para facilitar a identificação
        # de uma possível espera em HTTP, banco, lock etc.
        if tempo_sem_progresso >= 60:
            print(
                "[ALERTA] Nenhuma tarefa terminou há {:.0f}s. "
                "Dump das threads:"
                .format(tempo_sem_progresso),
                flush=True
            )

            try:
                faulthandler.dump_traceback()
            except Exception as e:
                print(
                    "[ERRO] Não foi possível gerar dump das threads: {}"
                    .format(e),
                    flush=True
                )


def _iniciar_monitor(total, nome_processo):
    """
    Cria o estado utilizado pelo monitor.
    """
    lock = threading.Lock()
    concluidos = [0]
    ultimo_progresso = [time_module.time()]

    thread_monitor = threading.Thread(
        target=_monitorar_progresso,
        args=(
            total,
            concluidos,
            ultimo_progresso,
            nome_processo,
            lock
        )
    )

    thread_monitor.daemon = True
    thread_monitor.start()

    return lock, concluidos, ultimo_progresso


# ---------------------------------------------------------
# PROCESSAMENTO PRINCIPAL
# ---------------------------------------------------------

def mathc_process(self):

    info_tipo_ = 1  # heterônimo
    info_tipo = 2  # homônimo

    retorno_dados = []
    list_found = []
    lista_n_found = []
    lista_homonimos = []
    lista_cnt_localizado = []

    contador_macth = defaultdict(lambda: {
        "FOUND": 0,
        "N_EN": 0,  # JA NA BASE
        "ERROR": 0,
        "QTPUSH": 0,
        "UPDATE": 0,
        "UPDATE_NAME": 0,
    })

    # LISTA COM O NOME E DATA DE NASCIMENTO
    retorno_nome = full_dados(self)

    if not retorno_nome:
        return None

    try:

        dados_tabela = pd.DataFrame(retorno_nome)
        batch_size = self.process_lote
        total = len(dados_tabela)

        print(
            "Total de registros para processar: {}".format(total),
            flush=True
        )

        # Um executor é mantido para todos os lotes.
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            total_processado = 0

            for start in range(0, total, batch_size):

                bloco = dados_tabela.iloc[
                    start:start + batch_size
                ]

                print(
                    "Processando registros {} até {} de {}".format(
                        start + 1,
                        min(start + batch_size, total),
                        total
                    ),
                    flush=True
                )

                futures = {}

                # SUBMETE TODAS AS TAREFAS DO LOTE PRIMEIRO.
                # Não chamar future.result() aqui.
                for _, registro in bloco.iterrows():

                    result_exists = executor.submit(
                        search_from_name_obito,
                        self,
                        limpar_nome_rn(registro['nome']),
                        registro['data_nascimento'],
                        registro['obito_id'],
                        registro
                    )

                    futures[result_exists] = registro['obito_id']

                total_lote = len(futures)

                lock, concluidos, ultimo_progresso = _iniciar_monitor(
                    total_lote,
                    "BUSCA DE ÓBITOS"
                )

                inicio_lote = time_module.time()

                # Agora recebemos os resultados conforme cada thread termina.
                for result_exists in as_completed(futures):

                    obito_id = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        lista_cnt_localizado.append(resultado)

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        tempo = time_module.time() - inicio_lote

                        print(
                            "[OK] obito_id={} | lote {}/{} | {:.2f}s".format(
                                obito_id,
                                concluidos[0],
                                total_lote,
                                tempo
                            ),
                            flush=True
                        )

                    except Exception as e:

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[ERRO] obito_id={} -> {}".format(
                                obito_id,
                                str(e)
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "ERRO obito_id={} NA BUSCA:\n{}".format(
                                obito_id,
                                traceback.format_exc()
                            )
                        )

                total_processado += total_lote

                print(
                    "[LOTE FINALIZADO] {}/{} registros processados".format(
                        total_processado,
                        total
                    ),
                    flush=True
                )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar nomes: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO DA BUSCA DOS DADOS {}".format(
                str(e)
            )
        )

    try:

        for result_lista in lista_cnt_localizado:

            if not isinstance(result_lista, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_lista
                    )
                )

                continue

            if result_lista.get('status') == 'n_encontrado':

                print(
                    "Lista com os dados não encontrado {}".format(
                        result_lista
                    ),
                    flush=True
                )

                contador_macth['n_encontrado']["N_EN"] += 1

                lista_n_found.append(result_lista)

                ClassLogger.logging.error(
                    "Lista com os dados não encontrado {}".format(
                        result_lista
                    )
                )

                continue

            if result_lista.get('status') == 'homonimo':

                contador_macth['homonimo']["ERROR"] += 1

                lista_homonimos.append(result_lista)

                ClassLogger.logging.error(
                    "Lista com os homonimos {}".format(
                        result_lista
                    )
                )

                continue

            if result_lista.get('status') == 'sucesso':

                contador_macth['sucesso']["FOUND"] += 1

                list_found.append(result_lista)

        lista_error_he = []
        lista_error_ho = []

        if lista_n_found:
        
            # VOU PRECESSAR OS NOMES NÃO LOCALIZADO INSERI NA BASE
            # E ENVIAR UM E-MAIL COM ANEXO
            process_nfound(self, lista_n_found)

        if  lista_homonimos:
        
            contador_homonimos, lista_error_ho = process_homonimos(
                self,
                lista_homonimos
            )
        
            retorno_dados.append({
                'homonimos':
                    contador_homonimos.get('sucesso_homonimos')
            })

        # ENVIO A LISTA PARA PROCESSAR ATUALIZAR OS DADOS
        if list_found:

            contador_heteronimo, lista_error_he = process_found(
                self,
                list_found
            )

            retorno_dados.append({
                'heteronimo':
                    contador_heteronimo.get('sucesso_heteronimo')
            })

        lista_error_he.extend(lista_error_ho)

        return retorno_dados, lista_error_he

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar o Exists lista_cnt_localizado: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO RESULT EXISTS "
            "lista_cnt_localizado {}".format(str(e))
        )


# ---------------------------------------------------------
# PROCESSA OS ENCONTRADOS
# ---------------------------------------------------------

def process_found(self, lista_found):

    print(
        "----------------------***----------",
        flush=True
    )

    list_info_update = []
    list_error = []
    update_ob_localizado = []

    contador_ = defaultdict(lambda: {
        "ATUALIZADO": 0,
        "N_ENCONTRADO": 0,  # JA NA BASE
        "ERROR_ATUALIZAR": 0
    })

    if not lista_found:
        return contador_, list_error

    dados_tabela_found = pd.DataFrame(lista_found)

    try:

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor_found:

            dados_tabela_found = pd.DataFrame(lista_found)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)

            print(
                "Total de registros para processar: {}".format(
                    total_found
                ),
                flush=True
            )

            total_processado = 0

            for start in range(0, total_found, batch_size_found):

                bloco_found = dados_tabela_found.iloc[
                    start:start + batch_size_found
                ]

                print(
                    "Processando registros {} até {} de {}".format(
                        start + 1,
                        min(start + batch_size_found, total_found),
                        total_found
                    ),
                    flush=True
                )

                futures = {}

                for _, registro_bloco in bloco_found.iterrows():

                    print(
                        "LISTA PARA PROCESSAR OS DADOS APROVEITADOS....",
                        flush=True
                    )

                    print(
                        "obito_id={} CPF={}".format(
                            registro_bloco.get('id_obito'),
                            registro_bloco.get('CPF')
                        ),
                        flush=True
                    )

                    if (
                        registro_bloco['CPF'] is None
                        or pd.isna(registro_bloco['CPF'])
                    ):

                        print(
                            "CPF ausente para o registro: {}".format(
                                registro_bloco
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "CPF ausente para o registro: {}".format(
                                registro_bloco
                            )
                        )

                        contador_['erro_heteronimo'][
                            "ERROR_ATUALIZAR"
                        ] += 1

                        list_error.append({
                            "obito_id": registro_bloco.get('id_obito')
                        })

                        continue

                    result_exists = executor_found.submit(
                        push_cpf_obito,
                        self,
                        registro_bloco['CPF'],
                        registro_bloco['id_obito'],
                        registro_bloco,
                        auxliares.HETERENOMIO
                    )

                    futures[result_exists] = registro_bloco['id_obito']

                total_lote = len(futures)

                if not total_lote:
                    continue

                lock, concluidos, ultimo_progresso = _iniciar_monitor(
                    total_lote,
                    "ATUALIZAÇÃO HETERÔNIMO"
                )

                inicio_lote = time_module.time()

                for result_exists in as_completed(futures):

                    obito_id = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        list_info_update.append(resultado)

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[OK UPDATE] obito_id={} | {}/{}".format(
                                obito_id,
                                concluidos[0],
                                total_lote
                            ),
                            flush=True
                        )

                    except Exception as e:

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[ERRO UPDATE] obito_id={} -> {}".format(
                                obito_id,
                                str(e)
                            ),
                            flush=True
                        )

                        list_error.append({
                            "obito_id": obito_id
                        })

                        ClassLogger.logging.error(
                            "ERRO NO UPDATE obito_id={}:\n{}".format(
                                obito_id,
                                traceback.format_exc()
                            )
                        )

                total_processado += total_lote

                print(
                    "[LOTE UPDATE FINALIZADO] {}/{}".format(
                        total_processado,
                        total_found
                    ),
                    flush=True
                )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar update nos nomes NO PROCESSO FOUND: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {}".format(
                str(e)
            )
        )

    try:

        if not list_info_update:
            return contador_, list_error

        for result_sucesso in list_info_update:

            if not isinstance(result_sucesso, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_sucesso
                    )
                )

                continue

            if result_sucesso.get('status') == 'erro':

                contador_['erro_heteronimo'][
                    "ERROR_ATUALIZAR"
                ] += 1

                list_error.append({
                    "obito_id": result_sucesso.get('id_obito')
                })

                continue

            if result_sucesso.get('status') == 'sucesso':

                print(
                    "ESTAOU SAINDO NO SUCESSO AO ATUALIZAR",
                    flush=True
                )

                contador_['sucesso_heteronimo'][
                    "ATUALIZADO"
                ] += 1

                update_ob_localizado.append(
                    result_sucesso
                )

        return contador_, list_error

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar update nos nomes: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {}".format(
                str(e)
            )
        )


# ---------------------------------------------------------
# PROCESSA HOMÔNIMOS
# ---------------------------------------------------------

def process_homonimos(self, l_homonimos):

    list_info_update = []
    list_error = []
    update_ob_localizado = []

    contador_ = defaultdict(lambda: {
        "ATUALIZADO": 0,
        "N_ENCOTRATO": 0,  # JA NA BASE
        "ERROR_ATUALIZAR": 0
    })

    if not l_homonimos:
        return contador_, list_error

    dados_tabela_found = pd.DataFrame(l_homonimos)

    try:

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor_found:

            dados_tabela_found = pd.DataFrame(l_homonimos)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)

            print(
                "Total de registros para processar: {}".format(
                    total_found
                ),
                flush=True
            )

            total_processado = 0

            for start in range(0, total_found, batch_size_found):

                bloco_found = dados_tabela_found.iloc[
                    start:start + batch_size_found
                ]

                print(
                    "Processando registros {} até {} de {}".format(
                        start + 1,
                        min(start + batch_size_found, total_found),
                        total_found
                    ),
                    flush=True
                )

                futures = {}

                for _, registro_bloco in bloco_found.iterrows():

                    result_exists = executor_found.submit(
                        push_cpf_obito,
                        self,
                        None,
                        registro_bloco['id_obito'],
                        registro_bloco,
                        auxliares.HOMONIMOS
                    )

                    futures[result_exists] = registro_bloco['id_obito']

                total_lote = len(futures)

                if not total_lote:
                    continue

                lock, concluidos, ultimo_progresso = _iniciar_monitor(
                    total_lote,
                    "ATUALIZAÇÃO HOMÔNIMOS"
                )

                for result_exists in as_completed(futures):

                    obito_id = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        list_info_update.append(resultado)

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[OK HOMÔNIMO] obito_id={} | {}/{}".format(
                                obito_id,
                                concluidos[0],
                                total_lote
                            ),
                            flush=True
                        )

                    except Exception as e:

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[ERRO HOMÔNIMO] obito_id={} -> {}".format(
                                obito_id,
                                str(e)
                            ),
                            flush=True
                        )

                        list_error.append({
                            "obito_id": obito_id
                        })

                        ClassLogger.logging.error(
                            "ERRO HOMÔNIMO obito_id={}:\n{}".format(
                                obito_id,
                                traceback.format_exc()
                            )
                        )

                total_processado += total_lote

                print(
                    "[LOTE HOMÔNIMOS FINALIZADO] {}/{}".format(
                        total_processado,
                        total_found
                    ),
                    flush=True
                )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar update nos nomes: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {}".format(
                str(e)
            )
        )

    try:

        if not list_info_update:
            return contador_, list_error

        for result_sucesso in list_info_update:

            if not isinstance(result_sucesso, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_sucesso
                    )
                )

                continue

            if result_sucesso.get('status') == 'erro':

                contador_['erro_homonimos'][
                    "ERROR_ATUALIZAR"
                ] += 1

                list_error.append({
                    "obito_id": result_sucesso.get('id_obito')
                })

                ClassLogger.logging.error(
                    "TENHO ERRO PARA REALIZAR O UPDATE {}".format(
                        result_sucesso
                    )
                )

                continue

            if result_sucesso.get('status') == 'sucesso':

                contador_['sucesso_homonimos'][
                    "ATUALIZADO"
                ] += 1

                update_ob_localizado.append(
                    result_sucesso
                )

        return contador_, list_error

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar update nos nomes: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF "
            "list_info_update {}".format(str(e))
        )


# ---------------------------------------------------------
# PROCESSA NÃO ENCONTRADOS
# ---------------------------------------------------------

def process_nfound(self, lista_notFound):

    list_up_n_encontrado = []

    try:

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor_found:

            dados_tabela_found = pd.DataFrame(lista_notFound)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)

            print(
                "Total de registros para processar: {}".format(
                    total_found
                ),
                flush=True
            )

            total_processado = 0

            for start in range(0, total_found, batch_size_found):

                bloco_found = dados_tabela_found.iloc[
                    start:start + batch_size_found
                ]

                print(
                    "Processando registros {} até {} de {}".format(
                        start + 1,
                        min(start + batch_size_found, total_found),
                        total_found
                    ),
                    flush=True
                )

                futures = {}

                for _, registro_bloco in bloco_found.iterrows():

                    result_exists = executor_found.submit(
                        push_cpf_obito,
                        self,
                        None,
                        registro_bloco['id_obito'],
                        registro_bloco,
                        auxliares.N_ENCONTRADO
                    )

                    futures[result_exists] = registro_bloco['id_obito']

                total_lote = len(futures)

                if not total_lote:
                    continue

                lock, concluidos, ultimo_progresso = _iniciar_monitor(
                    total_lote,
                    "ATUALIZAÇÃO NÃO ENCONTRADOS"
                )

                for result_exists in as_completed(futures):

                    obito_id = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        list_up_n_encontrado.append(resultado)

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[OK NÃO ENCONTRADO] obito_id={} | {}/{}".format(
                                obito_id,
                                concluidos[0],
                                total_lote
                            ),
                            flush=True
                        )

                    except Exception as e:

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[ERRO NÃO ENCONTRADO] obito_id={} -> {}".format(
                                obito_id,
                                str(e)
                            ),
                            flush=True
                        )

                        ClassLogger.logging.error(
                            "ERRO NÃO ENCONTRADO obito_id={}:\n{}".format(
                                obito_id,
                                traceback.format_exc()
                            )
                        )

                total_processado += total_lote

                print(
                    "[LOTE NÃO ENCONTRADOS FINALIZADO] {}/{}".format(
                        total_processado,
                        total_found
                    ),
                    flush=True
                )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar update nos nomes: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO UPDATE DOS CPF {}".format(
                str(e)
            )
        )

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

    df = pd.DataFrame(dados_estruturados)

    corpo_html = df.to_html(
        index=False,
        border=1,
        justify="center"
    )

    buffer_memoria = io.StringIO()

    df.to_csv(
        buffer_memoria,
        index=False,
        sep=';',
        encoding='utf-8-sig'
    )

    dados_csv_bytes = buffer_memoria.getvalue().encode(
        'utf-8-sig'
    )

    msg = (
        "LISTA COM DADOS NÃO ENCONTRADO NA PROSCORE\n"
        "com a quantidade de {}".format(
            len(dados_estruturados)
        )
    )

    enviar_email_all_anexo(
        msg,
        dados_csv_bytes,
        'relatorio_n_encontrato'
    )


# ---------------------------------------------------------
# PROCESSA ANO NÃO BATE
# ---------------------------------------------------------

def process_ano_n_bate(self, lista_found):

    list_info_update = []
    list_error = []
    update_ob_localizado = []

    contador_ = defaultdict(lambda: {
        "ATUALIZADO": 0,
        "N_ENCOTRATO": 0,  # JA NA BASE
        "ERROR_ATUALIZAR": 0
    })

    print(
        "ESTOU ACESSANDO O MATCH NAME",
        flush=True
    )

    if not lista_found:
        return contador_, list_error

    dados_tabela_found = pd.DataFrame(lista_found)

    try:

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor_found:

            dados_tabela_found = pd.DataFrame(lista_found)
            batch_size_found = self.process_lote
            total_found = len(dados_tabela_found)

            print(
                "Total de registros para processar: {}".format(
                    total_found
                ),
                flush=True
            )

            total_processado = 0

            for start in range(0, total_found, batch_size_found):

                bloco_found = dados_tabela_found.iloc[
                    start:start + batch_size_found
                ]

                print(
                    "Processando registros {} até {} de {}".format(
                        start + 1,
                        min(start + batch_size_found, total_found),
                        total_found
                    ),
                    flush=True
                )

                futures = {}

                for _, registro_bloco in bloco_found.iterrows():

                    result_exists = executor_found.submit(
                        push_cpf_obito,
                        self,
                        None,
                        registro_bloco['id_obito'],
                        registro_bloco,
                        auxliares.ANO_N_BATE
                    )

                    futures[result_exists] = registro_bloco['id_obito']

                total_lote = len(futures)

                if not total_lote:
                    continue

                lock, concluidos, ultimo_progresso = _iniciar_monitor(
                    total_lote,
                    "ATUALIZAÇÃO ANO NÃO BATE"
                )

                for result_exists in as_completed(futures):

                    obito_id = futures[result_exists]

                    try:

                        resultado = result_exists.result()

                        list_info_update.append(resultado)

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[OK ANO NÃO BATE] obito_id={} | {}/{}".format(
                                obito_id,
                                concluidos[0],
                                total_lote
                            ),
                            flush=True
                        )

                    except Exception as e:

                        with lock:
                            concluidos[0] += 1
                            ultimo_progresso[0] = time_module.time()

                        print(
                            "[ERRO ANO NÃO BATE] obito_id={} -> {}".format(
                                obito_id,
                                str(e)
                            ),
                            flush=True
                        )

                        list_error.append({
                            "obito_id": obito_id
                        })

                        ClassLogger.logging.error(
                            "ERRO ANO NÃO BATE obito_id={}:\n{}".format(
                                obito_id,
                                traceback.format_exc()
                            )
                        )

                total_processado += total_lote

                print(
                    "[LOTE ANO NÃO BATE FINALIZADO] {}/{}".format(
                        total_processado,
                        total_found
                    ),
                    flush=True
                )

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar process_ano_n_bate: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO NO process_ano_n_bate {}".format(
                str(e)
            )
        )

    try:

        if not list_info_update:
            return contador_, list_error

        for result_sucesso in list_info_update:

            if not isinstance(result_sucesso, dict):

                ClassLogger.logging.error(
                    "Resultado inválido na busca: {!r}".format(
                        result_sucesso
                    )
                )

                continue

            if result_sucesso.get('status') == 'erro':

                contador_['erro_heteronimo'][
                    "ERROR_ATUALIZAR"
                ] += 1

                list_error.append({
                    "obito_id": result_sucesso.get('id_obito')
                })

                ClassLogger.logging.error(
                    "TENHO ERRO PARA REALIZAR O UPDATE {}".format(
                        result_sucesso
                    )
                )

                continue

            if result_sucesso.get('status') == 'sucesso':

                contador_['sucesso_heteronimo'][
                    "ATUALIZADO"
                ] += 1

                update_ob_localizado.append(
                    result_sucesso
                )

        return contador_, list_error

    except Exception as e:

        erro_detalhado = traceback.format_exc()

        print(
            "Falha ao processar list_info_update::: {}".format(
                erro_detalhado
            ),
            flush=True
        )

        ClassLogger.logging.error(
            "ERRO LINHA PROCESSAMENTO list_info_update::: {}".format(
                str(e)
            )
        )
