from flask import Flask, flash, render_template, request, redirect, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "perritoalexis"

client = MongoClient("mongodb+srv://Raytest:raysito123@ralex.lbaspzb.mongodb.net/")
db = client["Tienda_Perritos"]
usuarios_collection = db["usuarios"]

@app.route('/')
def home():
    return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    usuario = usuarios_collection.find_one({
        "email": email
    })

    if usuario and check_password_hash(usuario["password"], password):
        session["usuario"] = email
        session["nombre"] = usuario["nombre"]

        flash("Inicio de sesión exitoso", "success")
        return redirect("/base")
    else:
        flash("Correo o contraseña incorrectos", "danger")
        return redirect("/login")
    
@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        password_hash = generate_password_hash(password)
        edad = request.form.get("edad")
        genero = request.form.get("genero")

        usuario_existente = usuarios_collection.find_one({"email": email})

        if usuario_existente:
            flash("El usuario ya existe")
            return redirect("/registrar")

        usuarios_collection.insert_one({
            "nombre": nombre,
            "email": email,
            "password": password_hash,
            "edad": edad,
            "genero": genero
        })

        session["usuario"] = email
        session["nombre"] = nombre
        flash("Registro exitoso", "success")
        return redirect("/base")    
    return render_template("registro.html")

@app.route("/recuperar", methods=["POST"])
def recuperar():
    email = request.form.get("email")

    usuario = usuarios_collection.find_one({"email": email})

    if usuario:
        token = secrets.token_urlsafe(32)  # 👈 generas token

        usuarios_collection.update_one(   # 👈 AQUÍ VA
            {"email": email},
            {"$set": {
                "reset_token": token
            }}
        )

        enviar_correo(email, token)  # 👈 mandas el correo

    flash("Si el correo existe, se envió un enlace", "info")
    return redirect("/login")

@app.route("/base")
def base():
    if "usuario" not in session:
        flash("Debes iniciar sesión para acceder a esta página", "warning")
        return redirect("/login")
    
    return render_template("base.html")

if __name__ == '__main__':
    app.run(debug=True)