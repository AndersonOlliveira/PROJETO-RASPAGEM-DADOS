
from urllib.parse import urljoin
from utils.data import obter_ultimos_dias

def extrair_links(soup,url):

    print('SAINDO PARA EXTRAIR LINKS DO FORMS PONTA GROSSA')

    url_s = []
    form = soup.find("form", {"name": "form1"})


    if form:
        action = form.get("action")
        input_data = form.find("input", {"name": "ontem"})
        # print(f"FORM LOCALIAZADO {input_data}")

        if input_data:
            data = input_data.get("value")

        urls = urljoin("https://app.pontagrossa.pr.gov.br/",
                       action)

        for dias in obter_ultimos_dias():
            url_s.append({'links': urls, 'playload': dias})

    
    return url_s 

    

