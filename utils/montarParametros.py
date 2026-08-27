from datetime import datetime
from itertools import product
from urllib.parse import urljoin
from urllib.parse import urlencode

def gerar_urls_ggo(url_base):

    urls = []
    parametros = []

    ano_atual = datetime.now().year
    # dez_anos=  [ano for ano in range(ano_atual - 9, ano_atual + 1)]
    # meses =  [mes for mes in range(1,13)]
    # print(dez_anos)
    # print(meses)
    lista_param = {
         "mes": [mes for mes in range(1,3)],
         "ano":  [ano for ano in range(ano_atual - 1, ano_atual + 1)]
        #  "ano": [ano_atual
    }

    # print(lista_param)

    visitadas = set()
    for ano, mes in product(lista_param["ano"], lista_param["mes"]):
        params = urlencode({"mes": mes, "ano": ano})
        url = f"{url_base}?{params}"

        # Evita duplicação usando conjunto
        if url not in visitadas:
            urls.append(url)
            visitadas.add(url)

    # urljoin(meses)
    
    return urls