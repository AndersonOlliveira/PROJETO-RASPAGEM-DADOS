from flask import Blueprint
from api.controllers.crawler_controller import executor

api = Blueprint("api",__name__)

api.route("/crawler/aracatuba", methods=["GET"])(executor)