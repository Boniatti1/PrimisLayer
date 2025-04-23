from flask import Flask, request, jsonify

app = Flask(__name__)
ROUTES_PATH = "/etc/nginx/protected_routes.conf"

@app.route("/")
def index():
    with open(ROUTES_PATH) as f:
        rules = f.read()
    return jsonify(rules)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
