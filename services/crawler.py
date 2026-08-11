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


def iniciar_olds(self, servidor):

    try:
        nome = servidor["nome"]
        url_base = servidor["url"]
        parsers = servidor["parser"]
        paginacao = servidor["pagination"]
        nav = servidor["pagin"]
        parametros = servidor["parametros"]

        pasta, pasta_ERRO = verificar_pasta("arquivos", nome)
        preparar_pasta(pasta)

        fila = []

        if parametros:
            fila.extend(gerar_urls_ggo(url_base))
        else:
            fila.append(url_base)

        visitadas = set()

        while fila and len(visitadas) < 16:

            # Pega um lote de URLs
            lote = []

            while fila:
                url = fila.pop(0)

                if url in visitadas:
                    continue

                if len(visitadas) >= 16:
                    break

                visitadas.add(url)
                lote.append(url)

            if not lote:
                break

            ClassLogger.logging.info(
                f"Processando lote com {len(lote)} URLs"
            )

            # ==========================================
            # 1. FAZER REQUESTS EM PARALELO
            # ==========================================

            with ThreadPoolExecutor(
                max_workers=self.max_workers
            ) as executor:

                futures = {
                    executor.submit(
                        self.client.get,
                        url
                    ): url
                    for url in lote
                }

                resultados = []

                for future in as_completed(futures):

                    url = futures[future]

                    try:
                        soup = future.result()

                        if soup is None:
                            ClassLogger.logging.warning(
                                f"Não foi possível obter: {url}"
                            )
                            continue

                        resultados.append(
                            (url, soup)
                        )

                    except Exception as e:

                        ClassLogger.logging.error(
                            f"Erro ao processar URL {url}: {e}",
                            exc_info=True
                        )

            # ==========================================
            # 2. PROCESSAR OS PARSERS
            # ==========================================

            for url, soup in resultados:

                try:

                    registros = parsers(
                        self,
                        soup
                    )

                    if registros:
                        salvar_csv(
                            registros=registros,
                            pasta=pasta,
                            nome=nome
                        )

                except Exception as e:

                    ClassLogger.logging.error(
                        f"Erro no parser {url}: {e}",
                        exc_info=True
                    )

                # ======================================
                # 3. DESCOBRIR PRÓXIMAS PÁGINAS
                # ======================================

                if paginacao:

                    try:

                        links = nav(
                            soup,
                            url
                        )

                        print(
                            f"Links encontrados em {url}: {links}"
                        )

                        if links:

                            for link in links:

                                if link in visitadas:
                                    continue

                                if link in fila:
                                    continue

                                if (
                                    len(visitadas)
                                    + len(fila)
                                    < 16
                                ):
                                    fila.append(link)

                    except Exception as e:

                        ClassLogger.logging.error(
                            f"Erro ao localizar páginas de {url}: {e}",
                            exc_info=True
                        )

        # ==========================================
        # FINALIZA
        # ==========================================

        self.client.salvar_erros(pasta)

        ClassLogger.logging.info(
            f"Finalizado servidor: {nome}"
        )

        self.stats.salvar(
            pasta,
            nome
        )

    except Exception as e:

        ClassLogger.logging.error(
            f"Erro fatal na execução: {e}",
            exc_info=True
        )

        enviar_email_all(
            f"Erro fatal na execução do processamento "
            f"do servidor {nome}: {e}"
        )

def processar_url(self, url, parser):
    try:
        ClassLogger.logging.info(f"Processando URL: {url}")

        soup = self.client.get(url)

        if soup is None:
            ClassLogger.logging.warning(
                f"Não foi possível obter a página: {url}"
            )
            return url, None

        registros = parser(self, soup)

        return url, registros

    except Exception as e:
        ClassLogger.logging.error(
            f"Erro ao processar URL {url}: {e}",
            exc_info=True
        )

        return url, None

def iniciar(self,servidor):
    try:
        
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
            if self.parar:
                ClassLogger.logging.warning(
                    f"Processamento de {nome} interrompido pelo usuário."
                )
                break

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

                url_base = fila.pop(0)

                if url_base in visitadas:
                    continue

                ClassLogger.logging.info(f"Processando {url_base}")

                visitadas.add(url_base)

            
                try:
                    soup = executor.submit(self.client.get, url_base).result()
                except KeyboardInterrupt as e:
                       ClassLogger.logging.info("\nEncerrando loop por comando do usuário Crawler Dados (Ctrl+C).")
                                            
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
                except KeyboardInterrupt as e:
                    ClassLogger.logging.info("\nEncerrando loop por comando do usuário Crawler Dados (Ctrl+C).")
                                
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
                            if self.parar:
                                 break
                            for link in links:
                                # if link not in visitadas and len(visitadas) == 100:
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



