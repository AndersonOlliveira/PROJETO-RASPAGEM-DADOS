import pandas as pd
from pathlib import Path 


def salvar_erros(erros, pasta):

    if not erros:
        return

    arquivo = Path(pasta) / "erros.csv"

    pd.DataFrame(erros).to_csv(
        arquivo,
        sep=";",
        encoding="utf-8-sig",
        index=False
    )