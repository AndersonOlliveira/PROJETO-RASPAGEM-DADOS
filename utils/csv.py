import pandas as pd
from pathlib import Path
from utils.info_pastas import verificar_pasta
from Logs import ClassLogger
from datetime import datetime


# CSV = Path("tabela_populada.csv")
def salvar_csv(registros, pasta, nome):

    try:

        if not registros:
            return

        dia = datetime.now().strftime("%d-%m-%Y")

        arquivo = pasta / f"{nome}_{dia}.csv"

        df = pd.DataFrame(registros)

        df.to_csv(
            arquivo,
            sep=";",
            encoding="utf-8-sig",
            mode="a",
            header=not arquivo.exists(),
            index=False
        )

        ClassLogger.logging.info(
            f"Registros adicionados em: {arquivo}"
        )

    except Exception as e:

        ClassLogger.logging.error(
            f"Erro ao salvar CSV: {e}",
            exc_info=True
        )