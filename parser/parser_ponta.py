import re
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
            for lista_original in links.values():
                print(f"MEU URL COM OS LINK {lista_original}")

                detalhe = self.client.get(lista_original["LINKS"])

                if detalhe is None:
                    continue

                retorno_montagem = montar_dados(detalhe, lista_original)

                # print(f"Registro extraido: {retorno_montagem}")

                if isinstance(retorno_montagem, list):
                        registros.extend(retorno_montagem)
                elif retorno_montagem:
                        registros.append(retorno_montagem)

            # print("RESULTADO")
            # print(registros)

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
            # print(f"REGISTROS EXTRAIDOS {registros}")
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

        linhas = tabela_principal.find_all("tr", class_=["linhaclara", "linhaescura"])
        
        # print(f"Total de linhas encontradas: {len(linhas)}")
        
        for linha in list(linhas):
            link = linha.find("a", href=True)

          
            if link and link.has_attr('title'):
                texto_title = link['title'].strip()
                # texto = texto_title.get_text(strip=True)
                # print(f"Informação do Title: {texto_title}")
                # nascimento = re.search(texto).group()
                datas = re.findall(r"\d{2}/\d{2}/\d{4}", texto_title)
                # print(f"Informação do Title: {nascimento}")
                # print(f"Informação do Title: {datas}")

            else:
                print("Nenhum title encontrado para esta linha.")

           
            dados = [td.get_text(strip=True) for td in linha.find_all("td")]
            # if dados and dados[0] != "Nome":
            # if dados:
            #    results ={
            #      "NOME": dados[0] if len(dados[0]) > 0 else "",
            #      "DATA_NASCIMENTO" :datas[0],
            #      "SEXO": dados[1],
            #      "DATA_SEPULTAMENTO": dados[2] if len(dados[2]) > 0 else "",
            #      "HORA": dados[3] if len(dados[3]) > 1 else "",
            #      "CEMITERIO": dados[4] if len(dados[4]) > 1 else "",
            #      "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M")
                 
            #     }
              
            

            # if dados and dados[0] != "Nome" and dados[1] != "Sexo" and dados[2] != "Data Sepultamento" and dados[3] != "Cemitério" and dados[4] != "Mais Detalhes" :
            #     print(dados[0])
            #     print(dados[1])
            #     print(dados[2])
            #     print(dados[3])
            #     print(dados[4])

            

            # for result in dados:
                

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
                 "NOME": dados[0] if len(dados[0]) > 0 else "",
                 "DATA_NASCIMENTO" :datas[0],
                 "SEXO": dados[1],
                 "DATA_SEPULTAMENTO": dados[2] if len(dados[2]) > 0 else "",
                 "HORA": dados[3] if len(dados[3]) > 1 else "",
                 "CEMITERIO": dados[4] if len(dados[4]) > 1 else "",
                 "DATA_CAPTURA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                 "LINKS": full_url,
            })

            

        return results
    except Exception as e:
            ClassLogger.logging.error(f"Erro fatal na execução: {e}",exc_info=True)
            return [] 


def montar_dados(soup,dados_lista_principal):
    try:
        CAMPOS_IGNORADOS = {
                "",
                "DADOS DO FALECIDO",
                "SERVIÇO FUNERÁRIO MUNICIPAL DE PONTA GROSSA",
                "RUA THEODORO ROSAS, 1226 - FONE 3220-1080 RAMAIS 2164 E 2163"
            }

    
        dados_alinhados = {
            'NOME': dados_lista_principal.get('NOME', ''),
            'DATA_NASCIMENTO': dados_lista_principal.get('DATA_NASCIMENTO', ''),
            'SEXO': dados_lista_principal.get('SEXO', ''),
            'DATA_SEPULTAMENTO': dados_lista_principal.get('DATA_SEPULTAMENTO', ''),
            'HORA_SEPULTAMENTO': dados_lista_principal.get('HORA', ''),
            'CEMITERIO': dados_lista_principal.get('CEMITERIO', ''),
            'DATA_CAPTURA': dados_lista_principal.get('DATA_CAPTURA', ''),
            'LINKS': dados_lista_principal.get('LINKS', ''),
            'APELIDO_ALCUNHA': '',
            'PROFISSAO': '',
            'NATURALIDADE': '',
            'DATA_FALECIMENTO': '',
            'LOCAL_VELORIO': '',
            'LOCAL_FALECIMENTO': '',
            'FUNERARIA': '',
            'CARTORIO': '',
            'TUMULO_ALA': ''
        }
        
        linhas = soup.find_all("tr")

        for linha in linhas:
            colunas = linha.find_all("td")

            if not colunas or len(colunas) < 2:
                continue

            if colunas[0].get("align") != "right":
                continue

            chave_bruta = colunas[0].get_text(" ", strip=True).replace(":", "").upper()
            chave_bruta = " ".join(chave_bruta.split())

            print(f"MINHA CHAVES BRUTAAS {chave_bruta}")

            if chave_bruta in CAMPOS_IGNORADOS:
                continue

            valor = colunas[1].get_text(" ", strip=True).upper()

            if "SEXO" in chave_bruta.upper():
                match = re.search(r"IDADE:\s*(\d+)\s*ANOS", valor)

                if match:
                    idade = match.group(1)
                else:
                    idade = ""

                
                dados_alinhados['IDADE'] = idade
                
                if "MASCULINO" in valor or "MASC" in valor:
                    dados_alinhados['SEXO'] = "MASCULINO"
                elif "FEMININO" in valor or "FEM" in valor:
                    dados_alinhados['SEXO'] = "FEMININO"

            
                
            elif "PROFISSÃO" in chave_bruta:
                if "NATURALIDADE" in valor:
                    partes = valor.split("NATURALIDADE")
                    dados_alinhados['PROFISSAO'] = partes[0].replace(":", "").strip()
                    dados_alinhados['NATURALIDADE'] = partes[1].replace(":", "").strip()
                else:
                    dados_alinhados['PROFISSAO'] = valor

                 

            elif "DATA DE FALECIMENTO" in chave_bruta:
                dados_alinhados['DATA_FALECIMENTO'] = valor.split(" ")[0].strip()

            elif "CEMITÉRIO" in chave_bruta:
                dados_alinhados['TUMULO_ALA'] = valor.replace("BARRA DOS ANDRADES", "").strip()

            elif "LOCAL DE VELÓRIO" in chave_bruta or "VELORIO" in chave_bruta:
                dados_alinhados['LOCAL_VELORIO'] = valor

            elif "LOCAL DO FALECIMENTO" in chave_bruta:
                dados_alinhados['LOCAL_FALECIMENTO'] = valor

            elif "FUNERÁRIA" in chave_bruta:
                dados_alinhados['FUNERARIA'] = valor

            elif "CARTÓRIO" in chave_bruta:
                dados_alinhados['CARTORIO'] = valor

            elif "APELIDO/ALCUNHA" in chave_bruta:
                dados_alinhados['APELIDO_ALCUNHA'] = valor

        return dados_alinhados

    except Exception as e:
        print(f"Erro ao alinhar dados: {e}", exc_info=True)
        return dados_lista_principal  # Retorna o original em caso de falha
        
   