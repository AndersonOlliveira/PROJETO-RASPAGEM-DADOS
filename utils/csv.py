import pandas as pd
from pathlib import Path
from Logs import ClassLogger
from datetime import datetime
from Mail.ClassMail import enviar_email_all

# CSV = Path("tabela_populada.csv")
def salvar_csv(registros, pasta, nome):
    # print(registros)
    print(pasta)
    print(nome)
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
            f"Registros sendo adicionados em: {arquivo}"
        )

    except Exception as e:

        ClassLogger.logging.error(
            f"Erro ao salvar CSV: {e}",
            exc_info=True
        )
        # enviar_email_all(f"Erro ao salvar CSV: {e}",exc_info=True)



def salvar_csv_error(registros, pasta, nome):
    try:
        # Se não houver registros, interrompe a execução
        if not registros:
            return

        # Converte a pasta (string) para um objeto Path
        pasta_path = Path(pasta)
        
        # Cria a pasta automaticamente caso ela não exista no computador
        pasta_path.mkdir(parents=True, exist_ok=True)

        # Gera o nome do arquivo com a data atual
        dia = datetime.now().strftime("%d-%m-%Y")
        arquivo = pasta_path / f"{nome}_{dia}.csv"

        # Converte os registros em DataFrame
        df = pd.DataFrame(registros)

        # Salva o arquivo CSV
        df.to_csv(
            arquivo,
            sep=";",
            encoding="utf-8-sig",
            mode="a",
            header=not arquivo.exists(),  # Só cria cabeçalho se o arquivo NÃO existir
            index=False
        )

        ClassLogger.logging.info(
            f"Registros sendo adicionados em: {arquivo}"
        )

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro ao salvar CSV: {e}",
            exc_info=True
        )