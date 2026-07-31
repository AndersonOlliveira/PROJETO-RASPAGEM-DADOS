import pandas as pd
from pathlib import Path 


def salvar_erros(self, pasta):

    if not self.erros:
        return

    arquivo = Path(pasta) / "erros.csv"

    pd.DataFrame(self.erros).to_csv(
        arquivo,
        sep=";",
        encoding="utf-8-sig",
        index=False
    )