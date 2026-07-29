from pathlib import Path
import pandas as pd

CSV = Path("tabela_populada.csv")

def salvar_csv(lista):

    if not lista:
        return

    df = pd.DataFrame(lista)

    df.to_csv(
        CSV,
        sep=";",
        encoding="utf-8-sig",
        mode="a",
        header=not CSV.exists(),
        index=False
    )