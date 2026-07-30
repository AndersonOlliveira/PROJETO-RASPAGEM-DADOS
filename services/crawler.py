from types import SimpleNamespace
from pathlib import Path
from utils.csv import salvar_csv
from Logs import ClassLogger


def iniciar(self,servidor):

    try:

        nome = servidor["nome"]
        url = servidor["url"]
        parsers = servidor["parser"]
        paginacao = servidor["pagination"]
        nav = servidor["pagin"]

        pasta = Path("arquivos") / nome
        pasta.mkdir(parents=True, exist_ok=True)

        fila = [servidor['url']]

        # print(fila)
        # return

        visitadas = set()


        while fila:

            url = fila.pop(0)

            if url in visitadas:
                continue

            ClassLogger.logging.info(f"Processando {url}")

            visitadas.add(url)

            soup =  self.client.get(url)

            if soup is None:
                ClassLogger.logging.warning(f"Não foi possível obter a página: {url}")
                continue

            registros = parsers(soup)

            if parsers is None:
               ClassLogger.logging.error(f"Nenhum parser configurado para {nome}")
               return
            
            salvar_csv(registros=registros,pasta=pasta,nome=nome)

            # # links = extrair_links(soup,url)
            links = nav(soup,url)
            print(f"links {links}")

            if paginacao:

                for link in links:

                    if link not in visitadas:

                        fila.append(link)

        ClassLogger.logging.info("Finalizado")
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        
        