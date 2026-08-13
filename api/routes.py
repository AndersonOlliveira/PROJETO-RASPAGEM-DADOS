from flask import Blueprint, request, jsonify
from api.controllers.crawler_controller import executor


api = Blueprint("api", __name__)


@api.route("/crawler/aracatuba", methods=["POST"])
def executar():
    arquivo = request.files.get("teste")
    print(arquivo)
    print(arquivo.filename)
    if arquivo is None:
        return jsonify({"error": "arquivo 'teste' não enviado"}), 400

    # Passa o arquivo para o executor e retorna o resultado
    resultado = executor(arquivo)
    return jsonify({"result": resultado})