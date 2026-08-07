from datetime import datetime
from Logs import ClassLogger
import re


def extrair_cards(self,soup):

    try:

        registros = []

        tabela_principal = soup.find(
            "table",
            id=lambda x: x and "dtlFalecimentos" in x
        )

        if not tabela_principal:
            return []

        tabelas = tabela_principal.find_all("table")

        for tabela in tabelas:

            def texto(id_parcial):

                campo = tabela.find(
                    "span",
                    id=lambda x: x and id_parcial in x
                )

                return campo.get_text(strip=True) if campo else ""

            # ignora tabelas que não são registros
            nome = texto("lblNome")
            if not nome:
                continue

            filiacao_texto = texto("lblFiliacao0")
            filiacao = [x.strip() for x in filiacao_texto.split("&")] if filiacao_texto else []

            match = re.search(r"\d{2}/\d{2}/\d{4}", texto("Label14"))
            data_falecimento = match.group() if match else ""

            registros.append({
                "ID": texto("lblFunId"),
                "NOME": nome,
                "IDADE": texto("lblIdade"),
                "FILIACAO_A": filiacao[0] if len(filiacao) > 0 else "",
                "FILIACAO_B": filiacao[1] if len(filiacao) > 1 else "",
                "PROFISSAO": texto("lblProfissao0"),
                "CAUSA_MORTE": texto("Label13"),
                "DATA_FALECIMENTO": data_falecimento,
                "DATA_FALECIMENTO_COMPLETO": texto("Label14"),
                "LOCAL_DO_FALECIMENTO": texto("Label15"),
                "LOCAL_DO_VELORIO": texto("Label16"),
                "LOCAL_DO_SEPULTAMENTO": texto("Label17"),
                "DATA_SEPULTAMENTO": texto("Label18"),
                "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

        ClassLogger.logging.info(f"{len(registros)} registros encontrados.")

        print(registros)

        return registros

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro fatal na execução: {e}",
            exc_info=True
        )
        return []