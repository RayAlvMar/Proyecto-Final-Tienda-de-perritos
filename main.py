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

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "perritostienda61@gmail.com"
EMAIL_PASSWORD = "njzd jlaa gwlr mqvs"


def enviar_correo(destinatario, token):
    link = f"http://127.0.0.1:5000/reset/{token}"

    mensaje = MIMEText(f"""
Hola.

Haz clic en el siguiente enlace para restablecer tu contraseña:

{link}

Si no solicitaste esto, ignora este correo.
""")

    mensaje["Subject"] = "Recuperación de contraseña"
    mensaje["From"] = EMAIL_SENDER
    mensaje["To"] = destinatario

    servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    servidor.starttls()
    servidor.login(EMAIL_SENDER, EMAIL_PASSWORD)

    servidor.sendmail(
        EMAIL_SENDER,
        destinatario,
        mensaje.as_string()
    )

    servidor.quit()

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
        return redirect("/login")    
    return render_template("registro.html")

@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():

    if request.method == "GET":
        return render_template("recuperar.html")

    email = request.form.get("email")

    usuario = usuarios_collection.find_one({"email": email})

    if usuario:
        token = secrets.token_urlsafe(32)

        usuarios_collection.update_one(
            {"email": email},
            {"$set": {"reset_token": token}}
        )

        enviar_correo(email, token)

    flash("Si el correo existe, se envió un enlace", "info")
    return redirect("/login")

@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    user = usuarios_collection.find_one({"reset_token": token})

    if not user:
        return "Token inválido"

    if request.method == "POST":
        nueva_password = request.form["password"]

        password_hash = generate_password_hash(nueva_password)

        usuarios_collection.update_one(
            {"reset_token": token},
            {
                "$set": {"password": password_hash},
                "$unset": {"reset_token": ""}
            }
        )

        return "Contraseña actualizada"

    return render_template("reset.html")

@app.route("/base")
def base():
    if "usuario" not in session:
        flash("Debes iniciar sesión para acceder a esta página", "warning")
        return redirect("/login")
    
    return render_template("base.html")

if __name__ == '__main__':
    app.run(debug=True)