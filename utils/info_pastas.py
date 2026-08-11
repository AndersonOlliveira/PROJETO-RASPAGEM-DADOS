
import re
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from Logs import ClassLogger
def verificar_pasta(nome_pasta,server):

    try:

    
        pasta_arquivos = Path(f"{nome_pasta}/{server}")
        pasta_arquivos.mkdir(parents=True, exist_ok=True)

      

        pasta_ERRO = Path(f"{nome_pasta}/error") 
        pasta_ERRO.mkdir(parents=True, exist_ok=True)

        return pasta_arquivos, pasta_ERRO

    except Exception as e:
        ClassLogger.logging.error(f"Falha na criação da pasta {e}" , exc_info=True)

def preparar_pasta(pasta):

    try:
        pasta = Path(pasta)

        pasta_old, pasta_error = verificar_pasta(pasta, "old")

        hoje = datetime.now().date()

        for arquivo in pasta.glob("*.csv"):

            # Arquivos que não devem ser movidos
            if arquivo.name in {"estatisticas.csv", "erros.csv"}:
                continue

            # Pega a data do nome:
            match = re.search(
                r"_(\d{2}-\d{2}-\d{4})\.csv$",
                arquivo.name
            )

            if not match:
                print(f"Arquivo sem data no nome: {arquivo.name}")
                continue

            data_arquivo = datetime.strptime(
                match.group(1),
                "%d-%m-%Y"
            ).date()

            print(
                f"Arquivo: {arquivo.name} | "
                f"Data: {data_arquivo} | "
                f"Hoje: {hoje}"
            )

            # Só move se for anterior a hoje
            if data_arquivo < hoje:

                destino = pasta_old / arquivo.name

                if destino.exists():
                    destino.unlink()

                arquivo.rename(destino)

                print(
                    f"Arquivo antigo movido para OLD: "
                    f"{arquivo.name}"
                )

    except Exception as e:

        ClassLogger.logging.error(
            f"Erro ao preparar pasta: {e}",
            exc_info=True
        )

def _extrair_data_nome(nome_arquivo):
    match = re.search(r"_(\d{2}-\d{2}-\d{4})\.csv$", nome_arquivo)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d-%m-%Y").date()
    except ValueError:
        return None


def _prefix_nome(nome_arquivo):
    match = re.search(r"^(.*)_\d{2}-\d{2}-\d{4}\.csv$", nome_arquivo)
    return match.group(1) if match else None

def abrir_arquivos(pasta):
    pasta = Path(pasta)
    hoje = datetime.now().date()
    pasta_old = pasta / "old"

    arquivos_antigos = {}

    if pasta_old.exists() and pasta_old.is_dir():
        for arquivo_antigo in pasta_old.glob("*.csv"):

            prefixo = _prefix_nome(arquivo_antigo.name)
            data_antiga = _extrair_data_nome(arquivo_antigo.name)

            if not prefixo or not data_antiga:
                continue

            atual = arquivos_antigos.get(prefixo)

            if not atual or data_antiga > atual[0]:
                arquivos_antigos[prefixo] = (
                    data_antiga,
                    arquivo_antigo
                )

    # Valores padrão
    registros_atual = 0
    diferenca = 0
    registros_antigo = 0

    for arquivo in pasta.iterdir():

        if arquivo.name.startswith('.'):
            continue

        if arquivo.name in {"old", "estatisticas.csv", "error"}:
            continue

        if not arquivo.is_file():
            continue

        data_arquivo = _extrair_data_nome(arquivo.name)

        if not data_arquivo:
            print(f"Arquivo sem data no nome: {arquivo.name}")
            continue

        if data_arquivo > hoje:
            print(f"Arquivo futuro ignorado: {arquivo.name}")
            continue

        print(
            f"Processando: {arquivo.name} | "
            f"Data: {data_arquivo}"
        )

        df_atual = pd.read_csv(
            arquivo,
            sep=";"
        )

        registros_atual = len(df_atual.index)

        print(
            f"Registros atuais: {registros_atual}"
        )

        prefixo = _prefix_nome(arquivo.name)

        if prefixo and prefixo in arquivos_antigos:

            data_antiga, arquivo_antigo = arquivos_antigos[prefixo]

            df_antigo = pd.read_csv(
                arquivo_antigo,
                sep=";"
            )

            registros_antigo = len(df_antigo.index)

            diferenca = (
                registros_atual -
                registros_antigo
            )

            print(
                f"Arquivo antigo encontrado: "
                f"{arquivo_antigo.name}"
            )

            print(
                f"Data antiga: {data_antiga}"
            )

            print(
                f"Registros antigos: "
                f"{registros_antigo}"
            )

            print(
                f"Crescimento: "
                f"{diferenca} registro(s)"
            )


        else:

            print(
                "Não há arquivo antigo para comparar."
            )

    return (
        registros_atual,
        diferenca,
        registros_antigo
    )
    
