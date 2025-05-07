from pathlib import Path
import json
import subprocess

# NGINX_CONF_PATH = Path(__file__).parent / "teste.conf"
NGINX_CONF_PATH = "/etc/nginx/protected_routes.conf"
NGINX_JSON_ROUTES_PATH = "/etc/nginx/protected_routes.json"

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
    try:
        subprocess.run(
            ["supervisorctl", "restart", "nginx"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        print(f"Erro: {e}")

def create_conf_file(paths):
    with open(NGINX_CONF_PATH, "w") as f:
        for path in paths:
            f.write(LOCATION_TEMPLATE.format(path=path))

def list_locations():
    with open(NGINX_JSON_ROUTES_PATH, "r") as f:
        reader = json.load(f)
        return reader["protected_routes"]


def delete_location(path):
    locations: list = list_locations()
    if not path in locations: return
    locations.remove(path)
    
    with open(NGINX_JSON_ROUTES_PATH, "w") as f:
        json.dump({"protected_routes": locations}, f)
    
    create_conf_file(locations)
    reload_nginx()

def add_location(path):
    locations: list = list_locations()
    if path in locations: return
    locations.append(path)
    
    with open(NGINX_JSON_ROUTES_PATH, "w") as f:
        json.dump({"protected_routes": locations}, f)
    
    create_conf_file(locations)
    reload_nginx()

