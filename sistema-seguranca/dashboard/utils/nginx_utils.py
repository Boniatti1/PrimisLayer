from pathlib import Path
import json
import subprocess
import re

NGINX_CONF_PATH = "/etc/nginx/protected_routes.conf"
NGINX_JSON_ROUTES_PATH = "/etc/nginx/protected_routes.json"


NGINX_LOGS_PATH = Path("/var/log/nginx")
NGINX_ERROR_PATH = NGINX_LOGS_PATH / "error.log"
NGINX_NORMAL_ACCESS = NGINX_LOGS_PATH / "normal_access.log"
NGINX_NORMAL_ERROR = NGINX_LOGS_PATH / "normal_error.log"
NGINX_PROTECTED_ACCESS = NGINX_LOGS_PATH / "protected_access.log"
NGINX_PROTECTED_ERROR = NGINX_LOGS_PATH / "protected_error.log"

LOCATION_TEMPLATE = """
location {path} {{
    include /etc/nginx/naxsi.rules;
    limit_req zone=req_limit_protected burst=1;

    access_log /var/log/nginx/protected_access.log;
    error_log /var/log/nginx/protected_error.log;

    if ($ssl_client_verify != SUCCESS) {{
        return 403;
    }}

    proxy_pass http://sistema:5000;
}}
"""


def reload_nginx():
    subprocess.run(
        ["supervisorctl", "restart", "nginx"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


# Funções para gerenciar as rotas protegidas


def list_locations():
    with open(NGINX_JSON_ROUTES_PATH, "r") as f:
        reader = json.load(f)
        return reader["protected_routes"]


def create_conf_file(paths):
    with open(NGINX_CONF_PATH, "w") as f:
        for path in paths:
            f.write(LOCATION_TEMPLATE.format(path=path))


def delete_location(path):
    locations: list = list_locations()
    if not path in locations:
        return
    locations.remove(path)

    with open(NGINX_JSON_ROUTES_PATH, "w") as f:
        json.dump({"protected_routes": locations}, f)

    create_conf_file(locations)
    reload_nginx()


def add_location(path):
    locations: list = list_locations()
    if path in locations:
        return
    locations.append(path)

    with open(NGINX_JSON_ROUTES_PATH, "w") as f:
        json.dump({"protected_routes": locations}, f)

    create_conf_file(locations)
    reload_nginx()


# Funções para leitura de logs


def tail_log_file(filepath, lines=100):
    with open(filepath, "r") as f:
        history = f.readlines()[-lines:]
        return history[::-1]


def parse_nginx_access(line):
    pattern = r'^(\d+\.\d+\.\d+\.\d+) .* \[(.*?)\] "(.*?) (.*?) HTTP\/.*?" (\d+) \d+ ".*?" "(.*?)"$'
    match = re.match(pattern, line)
    if not match:
        return None

    return {
        "ip": match.group(1),
        "date": match.group(2),
        "method": match.group(3),
        "url": match.group(4),
        "status": int(match.group(5)),
        "user_agent": match.group(6),
        "is_error": int(match.group(5)) >= 400,
    }


def parse_nginx_error(line):
    pattern = r"^(\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\d+#\d+): (.*)$"
    match = re.match(pattern, line)
    if not match:
        return None

    log_type = match.group(2).lower()
    badge_class = {
        "error": "danger",
        "warn": "warning",
        "notice": "info",
        "emerg": "purple",
    }.get(log_type, "secondary")

    return {
        "date": match.group(1),
        "log_type": log_type,
        "pid": match.group(3),
        "message": match.group(4),
        "badge_class": badge_class,
    }


def get_dict_logs():
    normal_access_logs = [
        parse_nginx_access(line) for line in tail_log_file(NGINX_NORMAL_ACCESS)
    ]
    normal_error_logs = [
        parse_nginx_error(line) for line in tail_log_file(NGINX_NORMAL_ERROR)
    ]
    protected_access_logs = [
        parse_nginx_access(line) for line in tail_log_file(NGINX_PROTECTED_ACCESS)
    ]
    protected_error_logs = [
        parse_nginx_error(line) for line in tail_log_file(NGINX_PROTECTED_ERROR)
    ]
    server_error_logs = [
        parse_nginx_error(line) for line in tail_log_file(NGINX_ERROR_PATH)
    ]

    return {
        "normal_access": normal_access_logs,
        "normal_errors": normal_error_logs,
        "protected_access": protected_access_logs,
        "protected_error": protected_error_logs,
        "server_errors": server_error_logs,
    }
