from datetime import datetime,timedelta,date
from Logs import ClassLogger
from parserPagina.pontaGrossa import extrair_links as parser_ponta
from utils.data import obter_ultimos_dias



def extrair_cards(self,soup):

        try:
            registros = []
            links = {}

            # # 1 - links da página de hoje
            for item in extrair_links(self, soup):
                links[item["LINKS"]] = item


            

            # 2 - páginas dos últimos dias
            lista_post = parser_ponta(soup, url=None)
            print(f"MINHA LISTA {lista_post}")

            post_processados = set()

            for post in lista_post:

                chave = post["playload"]

                if chave in post_processados:
                    continue

                post_processados.add(chave)

                print(f"MINHA CHAVES {chave} - URL {post['links']}")

                soup_post = self.client.post(
                    post["links"],
                    data={"ontem": post["playload"]}
                )

                if soup_post is None:
                    continue

                for item in extrair_links(self, soup_post):
                    links[item["LINKS"]] = item

            print(f"Total de links únicos: {len(links)}")

            # 3 - busca detalhes
            for url in links.values():

                detalhe = self.client.get(url["LINKS"])

                if detalhe is None:
                    continue

                retorno_montagem = montar_dados(detalhe, url)

                print(f"Registro extraido: {retorno_montagem}")

                if isinstance(retorno_montagem, list):
                        registros.extend(retorno_montagem)
                elif retorno_montagem:
                        registros.append(retorno_montagem)

            print("RESULTADO")
            print(registros)

            return registros
            
        except Exception as e:
               ClassLogger.logging.error(
                   f"Erro fatal na execução: {e}",
                   exc_info=True
               )
               return [] 


def processar_dados(self, soup):
        try:
            registros = self.extrair_cards(soup)
            print(f"REGISTROS EXTRAIDOS {registros}")
            return registros
        except Exception as e:
            ClassLogger.logging.error(
                f"Erro fatal na execução: {e}",
                exc_info=True
            )
            return []

def extrair_links(self,soup):
    try:
        links_seen = set()
        results = []
        tabela_principal = soup.find("table", class_="texto")
        if tabela_principal is None:
            return []

        linhas = tabela_principal.find_all("tr")
        for linha in linhas:
            link = linha.find("a", href=True)
            dados = [td.get_text(strip=True) for td in linha.select("td")]

            # print(dados)

            # skip if no link in this row
            if not link:
                continue

            href = link["href"]
            if not href.startswith("resumos.php"):
                continue

            # avoid duplicates
            if href in links_seen:
                continue
            links_seen.add(href)

            full_url = f"https://app.pontagrossa.pr.gov.br/sisppg/servico_funerario/internet/{href}"

            # include the row data together with the link so caller can associate them
            results.append({
                "COLS": dados,
                "LINKS": full_url,
            })

        return results
    except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {e}",exc_info=True)
            return [] 


def montar_dados(soup,url):
    try:
        CAMPOS_IGNORADOS = {
                "",
                "DADOS DO FALECIDO",
                "SERVIÇO FUNERÁRIO MUNICIPAL DE PONTA GROSSA",
                "RUA THEODORO ROSAS, 1226 - FONE 3220-1080 RAMAIS 2164 E 2163"
            }

        dados = {}
        linhas = soup.find_all("tr")

        for linha in linhas:

            print(f"MINHAS LINHAS PROCESSADAS")
            print(linha)
            colunas = linha.find_all("td")

            if colunas[0].get("align") != "right":
                continue

            if len(colunas) < 2:
                continue

            chave = colunas[0].get_text(" ", strip=True).replace(":", "").upper()
            valor = colunas[1].get_text(" ", strip=True).upper()
            dados['link']= url
            chave = " ".join(chave.split())

            if chave in CAMPOS_IGNORADOS:
                continue

            dados[chave] = valor

        return dados
    except Exception as e:
        ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)
        return {}   
   
     