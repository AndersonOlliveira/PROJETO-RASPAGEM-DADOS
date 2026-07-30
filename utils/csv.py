from pathlib import Path
import pandas as pd
from Logs import ClassLogger

# CSV = Path("tabela_populada.csv")

def salvar_csv(registros, pasta,nome):

    try:

        arquivo = pasta / f"{nome}.csv"

        if not registros:
            return

        df = pd.DataFrame(registros)
            
        df.to_csv(
            arquivo,
            sep=";",
            encoding="utf-8-sig",
            mode="a",
            header=not arquivo.exists(),
            index=False
        )

    except Exception as e:
         ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        