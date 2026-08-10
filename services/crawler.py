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

        # print(f"minha pasta retornada {pasta}")
        # print(f"minha pasta retornada {pasta_ERRO}")
      
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

            if parsers is None:
                ClassLogger.logging.error(f"Nenhum parser configurado para {nome}")
                return

            registros = parsers(self,soup)

            # if nav:
                
            #     ClassLogger.logging.warning(f"TENHO LINKS AQUI")
            #     for registro in registros:
            #         novos_registros = []
                    
            #         print(f"MEUS LINKS LOCALIZADOS PARA DETALHE {registro['LINKS']}")
            #         soup = self.client.get(registro['LINKS'])
            #         print(f"MEUS LINKS LOCALIZADOS PARA DETALHE {soup}")
            #         detalhe = parsers_links(soup)
            #         novos_registros.extend(detalhe)

            #         print(f"meus novos registros {novos_registros} ")

            #         registros = novos_registros
                

           
            
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
        self.stats.salvar(pasta_ERRO)
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
        enviar_email_all(f"Erro fatal na execução do processamento dos servidores: {e}", exc_info=True)

def Crawlers(servidor):
    print(f" NUMERO ENVIADO VIA API ::: {servidor}")

    return "TESTE PARA CONSULTA API"


        