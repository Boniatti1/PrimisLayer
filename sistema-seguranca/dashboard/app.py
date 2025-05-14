from flask import Flask, render_template, jsonify, request, abort, send_file
from utils.fail2ban_utils import get_fail2ban_logs
from utils.nginx_utils import delete_location, add_location, list_locations, get_dict_logs
from utils.certs_utils import (
    delete_client_cert,
    add_client_cert,
    get_client_p12_path,
    list_client_certs,
    get_certs_logs
)
import subprocess

app = Flask(__name__)

def telegram_alert(ip, action, level, msg=""):
    subprocess.run(["python", "/etc/scripts/telegram_alert.py", str(ip), str(action), str(level), str(msg)], check=True)
    

# Rotas principais


@app.route("/")
def dashboard():
    fail2ban_logs = get_fail2ban_logs()
    nginx_logs = get_dict_logs()
    certs_logs = get_certs_logs()

    return render_template("dashboard.html", fail2ban_logs=fail2ban_logs, **nginx_logs, certs_logs=certs_logs)


@app.route("/configurar", methods=["GET", "POST"])
def manage_config():
    routes = list_locations()
    certs = list_client_certs()

    return render_template("config.html", routes=routes, certs=certs)


# Rotas para gerenciar as rotas protegidas


@app.route("/rotas-protegidas", methods=["GET"])
def get_locations():
    return jsonify(list_locations())


@app.route("/rotas-protegidas", methods=["POST"])
def add_route():
    data = request.get_json()
    path = data.get("path")
    if not path or not path.startswith("/"):
        return jsonify({"error": "Path inválido"}), 400

    add_location(path)
    telegram_alert(request.remote_addr, "Nova rota protegida adicionada", "Baixa")

    return jsonify({"message": f"Path {path} adicionado"}), 201


@app.route("/rotas-protegidas", methods=["DELETE"])
def delete_route():
    data = request.get_json()
    path = data.get("path")
    if not path or not path.startswith("/"):
        return jsonify({"error": "Path inválido"}), 400

    delete_location(path)
    telegram_alert(request.remote_addr, "Rota protegida excluída", "Alta")

    return jsonify({"message": f"Path {path} removido"}), 200


# Rotas para gerenciar os certificados


@app.route("/certificados/remover/<string:name>")
def revoke_cert(name):
    r = delete_client_cert(name)
    telegram_alert(request.remote_addr, "Revogação de certificado", "Baixa")
    return str(r), 200


@app.route("/certificados/adicionar/<string:name>")
def add_cert(name):
    r = add_client_cert(name)
    telegram_alert(request.remote_addr, "Criação de novo certificado", "Média")
    return str(r), 200


@app.route("/certificados/download/<string:name>")
def download_p12(name):
    try:
        p12_path = get_client_p12_path(name)
        telegram_alert(request.remote_addr, "Download de um certificado", "Média")
        return send_file(
            str(p12_path),
            as_attachment=True,
            download_name=f"{name}.p12",
            mimetype="application/x-pkcs12",
        )   
    except FileNotFoundError as e:
        abort(404, description=str(e))
    except Exception as e:
        abort(500, description=f"Erro interno: {str(e)}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
