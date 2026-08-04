import re 
from Logs import ClassLogger
from datetime import datetime

def extrair_cards(self,soup):
    print(f"VOU SAIR AQUI COM O RESULTADO DA CONSULTA? DO GG INTERNO")
    registros = []

    try:
        cards = soup.find_all('div', class_="card-body p-4")

        for card in cards:
            registro = {}
            strong_tag = card.find("strong", class_="text-1 text-md")
            if strong_tag:
                nome = strong_tag.text.strip()
                registro["NOME"] = nome

            info_blocos = card.find_all("div", class_="text-sm")
            for bloco in info_blocos:
                titulo = bloco.find("strong", class_="text-1")
                conteudo = bloco.find("p")
                if titulo and conteudo:
                    chave = titulo.get_text(strip=True).upper()
                    valor = conteudo.get_text(" ", strip=True)
                    registro[chave] = valor.replace(" ", "/")

                # Datas (nascimento e falecimento)
                texto = card.get_text(" ", strip=True)
                datas = re.findall(r"\d{2}/\d{2}/\d{4}", texto)
                if len(datas) >= 2:
                    registro["DATA_NASCIMENTO"] = datas[0]
                    registro["DATA_FALECIMENTO"] = datas[1]

                registro["DATA_CAPTURA"] = datetime.now().strftime("%d/%m/%Y %H:%M")

                registros.append(registro)

        # print(registros)


        return registros
            
    except Exception as e:
         ClassLogger.logging.error(f"Erro fatal na execução: {e}", exc_info=True)        

