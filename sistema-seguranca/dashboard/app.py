from flask import Flask, render_template, jsonify, request, abort, send_file
from pathlib import Path
import re
from fail2ban_utils import get_fail2ban_logs
from nginx_utils import delete_location, add_location, list_locations
from certs_utils import delete_client_cert, add_client_cert, get_client_p12_path, list_client_certs

app = Flask(__name__)

# NGINX_LOGS_PATH = Path(__file__).parent.parent / "data" / "nginx"
NGINX_LOGS_PATH = Path("/var/log/nginx")
NGINX_ERROR_PATH = NGINX_LOGS_PATH / "error.log"      
NGINX_NORMAL_ACCESS = NGINX_LOGS_PATH / "normal_access.log" 
NGINX_NORMAL_ERROR = NGINX_LOGS_PATH / "normal_error.log"   
NGINX_PROTECTED_ACCESS = NGINX_LOGS_PATH / "protected_access.log" 
NGINX_PROTECTED_ERROR = NGINX_LOGS_PATH / "protected_error.log" 

def tail_log_file(filepath, lines=100):
    try:
        with open(filepath, 'r') as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        return []

def parse_nginx_access(line):
    pattern = r'^(\d+\.\d+\.\d+\.\d+) .* \[(.*?)\] "(.*?) (.*?) HTTP\/.*?" (\d+) \d+ ".*?" "(.*?)"$'
    match = re.match(pattern, line)
    if not match:
        return None
    
    return {
        'ip': match.group(1),
        'date': match.group(2),
        'method': match.group(3),
        'url': match.group(4),
        'status': int(match.group(5)),
        'user_agent': match.group(6),
        'is_error': int(match.group(5)) >= 400
    }

def parse_nginx_error(line):
    pattern = r'^(\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\d+#\d+): (.*)$'
    match = re.match(pattern, line)
    if not match:
        return None
    
    log_type = match.group(2).lower()
    badge_class = {
        'error': 'danger',
        'warn': 'warning',
        'notice': 'info',
        'emerg': 'purple'
    }.get(log_type, 'secondary')
    
    return {
        'date': match.group(1),
        'log_type': log_type,
        'pid': match.group(3),
        'message': match.group(4),
        'badge_class': badge_class
    }

@app.route('/')
def dashboard():
    normal_access_logs = [parse_nginx_access(line) for line in tail_log_file(NGINX_NORMAL_ACCESS) ]
    
    normal_error_logs = [parse_nginx_error(line) for line in tail_log_file(NGINX_NORMAL_ERROR)]  
    
    protected_access_logs = [parse_nginx_access(line) for line in tail_log_file(NGINX_PROTECTED_ACCESS)]
    
    protected_error_logs = [parse_nginx_error(line) for line in tail_log_file(NGINX_PROTECTED_ERROR)]
    
    server_error_logs = [parse_nginx_error(line) for line in tail_log_file(NGINX_ERROR_PATH)]
    
    fail2ban_logs = get_fail2ban_logs()
    
    return render_template(
        'dashboard.html',
        normal_access=normal_access_logs,
        normal_errors=normal_error_logs,
        protected_access=protected_access_logs,
        protected_errors=protected_error_logs,
        server_errors=server_error_logs,
        fail2ban_logs=fail2ban_logs
    )

@app.route("/locations", methods=["GET"])
def get_locations():
    return jsonify(list_locations())

@app.route("/locations", methods=["POST"])
def add_route():
    data = request.get_json()
    path = data.get("path")
    if not path or not path.startswith("/"):
        return jsonify({"error": "Path inválido"}), 400

    add_location(path)

    return jsonify({"message": f"Path {path} adicionado"}), 201

@app.route("/locations", methods=["DELETE"])
def delete_route():
    data = request.get_json()
    path = data.get("path")
    if not path or not path.startswith("/"):
        return jsonify({"error": "Path inválido"}), 400
    
    delete_location(path)

    return jsonify({"message": f"Path {path} removido"}), 200

@app.route("/rotas", methods=["GET", "POST"])
def manage_config():
    routes = list_locations()
    certs = list_client_certs()
    
    return render_template("config.html", routes=routes, certs=certs)

@app.route("/certificados/remover/<string:name>")
def revoke_cert(name):
    r = delete_client_cert(name)
    return str(r), 200
    
@app.route("/adicionar/<string:name>")
def add_cert(name):
    r = add_client_cert(name)
    return str(r), 200

@app.route('/certificados/download/<string:name>')
def download_p12(name):
    try:
        p12_path = get_client_p12_path(name)
        return send_file(
            str(p12_path),
            as_attachment=True,
            download_name=f"{name}.p12",
            mimetype="application/x-pkcs12"
        )
    except FileNotFoundError as e:
        abort(404, description=str(e)) 
    except Exception as e:
        abort(500, description=f"Erro interno: {str(e)}")
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)