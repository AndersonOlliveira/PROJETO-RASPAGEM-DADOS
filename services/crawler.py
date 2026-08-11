import calendar

from Logs import ClassLogger
from datetime import datetime
from utils.csv import salvar_csv
from types import SimpleNamespace
from urllib.parse import urlencode
from utils.erros import salvar_erros
from Mail.ClassMail import enviar_email_all
from utils.info_pastas import verificar_pasta, preparar_pasta
from utils.montarParametros import gerar_urls_ggo
from concurrent.futures import ThreadPoolExecutor, as_completed



def iniciar(self,servidor):
    try:
        # print(f"servidor enviad os {servidor}")


        # return

        nome = servidor["nome"]
        url_base = servidor["url"]
        parsers = servidor["parser"]
        paginacao = servidor["pagination"]
        nav = servidor["pagin"]
        parametros = servidor['parametros']
        # parsers_links = servidor['tdados']


        if nome:
            pasta, pasta_ERRO = verificar_pasta(f"arquivos",nome)
            preparar_pasta(pasta)
        
        fila = []

        # SE EXISTIR MONTO OS RARAMETROS 
        if parametros:
            fila.extend(gerar_urls_ggo(url_base))
        else:
            fila.append(url_base)
        visitadas = set()
        
        while fila:

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

                url_base = fila.pop(0)

                if url_base in visitadas:
                    continue

                ClassLogger.logging.info(f"Processando {url_base}")

                visitadas.add(url_base)
                try:
                    soup = executor.submit(self.client.get, url_base).result()
                except Exception as e:
                    ClassLogger.logger.error(f"Erro ao processar a URL: {e}", exc_info=True)
                    soup = None
                
                # links = nav(soup,url_base)
                # print(f"links {links}")


                if soup is None:
                    ClassLogger.logging.warning(f"Não foi possível obter a página: {url_base}")
                    continue

                if parsers is None:
                    ClassLogger.logging.error(f"Nenhum parser configurado para {nome}")
                    return


                try:
                    registros = executor.submit(parsers, self, soup).result()
                except Exception as e:
                    ClassLogger.logging.error(f"Erro ao processar paginas: {e}", exc_info=True)
                    registros = None

                # registros = parsers(self,soup)

            
                
                salvar_csv(registros=registros,pasta=pasta,nome=nome)

                # links = extrair_links(soup,url_base)
                if paginacao:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        try:
                            links = executor.submit(nav, soup, url_base).result()
                            print(f"links {links}")
                            for link in links:
                                # if link not in visitadas and len(visitadas) == 5:
                                if link not in visitadas:
                                    fila.append(link)

                        except Exception as e:
                            ClassLogger.logging.error(f"Erro ao processar paginas para localizar as páginas: {e}", exc_info=True)
                            links = None


                        # links = nav(soup,url_base)
                        # # print(f"links {links}")

                        # for link in links:

                        #     if link not in visitadas:

                        #         fila.append(link)
            self.client.salvar_erros(pasta)
            ClassLogger.logging.info("Finalizado")
            self.stats.salvar(pasta,nome)
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
        # enviar_email_all does not accept exc_info; pass only the message
        enviar_email_all(f"Erro fatal na execução do processamento dos servidores: {e}")

def Crawlers(servidor):
    print(f" NUMERO ENVIADO VIA API ::: {servidor}")

    return "TESTE PARA CONSULTA API"



