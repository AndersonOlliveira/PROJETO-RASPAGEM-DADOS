
import re
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
            # cliente_10-08-2026.csv
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