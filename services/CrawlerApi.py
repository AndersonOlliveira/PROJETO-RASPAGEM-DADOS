import os
from flask import Flask,request,jsonify,send_from_directory,send_file
class CrawlerApi:


    def executar(self,servidor,arquivo):

    
       return {
            "status": "ok",
            "servidor": servidor,
            "nome_arquivo":  arquivo.filename if arquivo else None
        }
