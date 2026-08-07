from flask import jsonify
from services.CrawlerApi import CrawlerApi



def executor():
    crawler = CrawlerApi()

    dados = crawler.executar(servidor=4)

    return jsonify(dados)