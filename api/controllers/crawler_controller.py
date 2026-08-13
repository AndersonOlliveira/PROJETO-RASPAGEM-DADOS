from flask import jsonify, json, request


from services.CrawlerApi import CrawlerApi



def executor(arquivo):
    crawler = CrawlerApi()

    dados = crawler.executar(servidor=5, arquivo=arquivo)
    
    # 3. Lembre-se de retornar os dados para a rota receber
    return dados
    


# async def receber_arquivo(file: UploadFile = File(...)):
#     # Ler o conteúdo do arquivo (Ex: em bytes)
#     conteudo = await file.read()
    
#     return JSONResponse(content={
#         "nome_arquivo": file.filename,
#         "tipo_arquivo": file.content_type,
#         "tamanho_bytes": len(conteudo),
#         "mensagem": "Arquivo recebido com sucesso!"
#     })