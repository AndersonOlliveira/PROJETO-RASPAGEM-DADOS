import calendar
from pathlib import Path
from Logs import ClassLogger
from datetime import datetime
from utils.montarParametros import gerar_urls_ggo
from urllib.parse import urlencode
from utils.csv import salvar_csv
from types import SimpleNamespace



def iniciar(self,servidor):

    try:

        nome = servidor["nome"]
        url_base = servidor["url"]
        parsers = servidor["parser"]
        paginacao = servidor["pagination"]
        nav = servidor["pagin"]
        parametros = servidor['parametros']

        pasta = Path("arquivos") / nome
        pasta.mkdir(parents=True, exist_ok=True)
        fila = []

        # SE EXISTIR MONTO OS RARAMETROS 
        if parametros:
          
            fila.extend(gerar_urls_ggo(url_base))
        else:
            fila.append(url_base)
                    
        
        # print(fila)
        # return

        visitadas = set()


        while fila:

            url_base = fila.pop(0)

            if url_base in visitadas:
                continue

            ClassLogger.logging.info(f"Processando {url_base}")

            visitadas.add(url_base)

            soup = self.client.get(url_base)
            # links = nav(soup,url_base)
            # print(f"links {links}")

            if soup is None:
                ClassLogger.logging.warning(f"Não foi possível obter a página: {url_base}")
                continue

            registros = parsers(soup)

            if parsers is None:
               ClassLogger.logging.error(f"Nenhum parser configurado para {nome}")
               return
            
            salvar_csv(registros=registros,pasta=pasta,nome=nome)


            

            # links = extrair_links(soup,url_base)
          

            if paginacao:
                links = nav(soup,url_base)
                print(f"links {links}")

                for link in links:

                    if link not in visitadas:

                        fila.append(link)
        self.client.salvar_erros(pasta)
        ClassLogger.logging.info("Finalizado")
        self.stats.salvar(pasta)
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        
        