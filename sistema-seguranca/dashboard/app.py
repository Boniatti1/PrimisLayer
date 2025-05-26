from flask import Flask, render_template, jsonify, request, abort, send_file
from utils.fail2ban_utils import get_fail2ban_logs
from utils.nginx_utils import delete_location, add_location, list_locations, get_dict_logs, nginx_alive, get_insights
from utils.certs_utils import (
    delete_client_cert,
    add_client_cert,
    get_client_p12_path,
    list_client_certs,
    get_certs_logs
)
from utils.naxsi_utils import get_naxsi_whitelist, get_optimized_rules, save_optimized_rules, activate_learning_mode, deactivate_learning_mode, learning_mode_active
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
    insights = get_insights()

    return render_template("dashboard.html", fail2ban_logs=fail2ban_logs, **nginx_logs, certs_logs=certs_logs, insights=insights)


@app.route("/configurar", methods=["GET", "POST"])
def manage_config():
    routes = list_locations()
    certs = list_client_certs()
    nginx_active = nginx_alive()
    learning_mode = learning_mode_active()

    return render_template("config.html", routes=routes, certs=certs, nginx_active=nginx_active, learning_mode=learning_mode)


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


# Rotas para o NAXSI


@app.route("/naxsi/optimized-rules")
def optimized_naxsi_rules():
    rules = get_optimized_rules()
    return jsonify({"rules": rules})


@app.post("/naxsi/save-rules")
def save_naxsi_whitelist():
    try:
        save_optimized_rules()
        telegram_alert(request.remote_addr, "Novas regras NAXSI foram geradas e aplicadas", "Alta")
        return "", 200
    except Exception as e:
        abort(500, description=f"Erro interno: {str(e)}")


@app.route("/naxsi/current-rules")
def current_naxsi_whitelist():
    rules = get_naxsi_whitelist()
    return jsonify({"rules": rules})


# Configurações do servidor


@app.route('/config/desligar-nginx', methods=['POST'])
def shutdown_nginx():
    try:
        result = subprocess.run(['supervisorctl', 'stop', 'nginx'], check=True, capture_output=True, text=True)
        telegram_alert(request.remote_addr, "O servidor foi desligado por painel", "Média")
        return "", 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.stderr.strip()}), 500


@app.route('/config/ligar-nginx', methods=['POST'])
def turn_on_nginx():
    try:
        result = subprocess.run(['supervisorctl', 'start', 'nginx'], check=True, capture_output=True, text=True)
        telegram_alert(request.remote_addr, "O servidor foi ativado por painel", "Média")
        return "", 200
    except subprocess.CalledProcessError as e:
        return jsonify({'error': e.stderr.strip()}), 500


@app.route('/config/ativar-aprendizado', methods=["POST"])
def naxsi_activate_learning_mode():
    try:
        activate_learning_mode()
        telegram_alert(request.remote_addr, "Modo aprendizado NAXSI ativado", "Crítica")
        return "", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/config/desativar-aprendizado', methods=["POST"])
def naxsi_deactivate_learning_mode():
    try:
        deactivate_learning_mode()
        telegram_alert(request.remote_addr, "Modo aprendizado NAXSI ativado", "Média")
        return "", 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
