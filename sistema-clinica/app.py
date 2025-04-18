from flask import Flask, render_template, request, redirect, url_for, jsonify
app = Flask(__name__)

doctor = {"user": "dr.silva", "password": "senha123", "nome": "Dr. Silva", "authorized": False}


records = {
    1: {"paciente": "João", "diagnostico": "Gripe", "doctor": "dr.silva", "data": "2023-10-01"},
    2: {"paciente": "Maria", "diagnostico": "Dor lombar", "doctor": "dr.ana", "data": "2023-10-02"}
}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        password = request.form.get("password")
        
        if user == doctor["user"] and doctor["password"] == password:
            doctor["authorized"] = True
            return redirect(url_for("list_records"))
        else:
            return "Usuário ou senha inválidos", 401
        
    return render_template("login.html")

@app.route("/prontuarios")
def list_records():
    if doctor["authorized"] == False:
        return "Não autorizado", 404
    
    return render_template("records.html",  prontuarios=records)

if __name__ == "__main__":
    app.run(debug=True, port=5000)