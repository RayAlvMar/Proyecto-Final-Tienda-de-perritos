from flask import Flask, flash, render_template, request, redirect, url_for, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import smtplib
import uuid
from bson.objectid import ObjectId
from email.mime.text import MIMEText
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "123456789"

client = MongoClient("mongodb+srv://Raytest:raysito123@ralex.lbaspzb.mongodb.net/")
db = client["Tienda_Perritos"]
usuarios_collection = db["usuarios"]
perros_collection = db["perros"]
carrito_collection = db["carrito"]

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

@app.before_request
def asignar_usuario():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

@app.route("/agregar_carrito/<id>", methods=["POST"])
def agregar_carrito(id):

    perro = perros_collection.find_one({"_id": ObjectId(id)})

    existente = carrito_collection.find_one({
        "usuario_id": session["user_id"],
        "producto_id": id
    })

    if existente:
        carrito_collection.update_one(
            {"_id": existente["_id"]},
            {"$inc": {"cantidad": 1}}
        )
    else:
        carrito_collection.insert_one({
            "usuario_id": session["user_id"],
            "producto_id": id,
            "nombre": perro["nombre"],
            "precio": perro.get("precio", 0),
            "imagen_url": perro["imagen_url"],
            "cantidad": 1
        })

    return redirect(url_for("adopcion"))

@app.route("/carrito")
def ver_carrito():

    carrito = list(
        carrito_collection.find({
            "usuario_id": session["user_id"]
        })
    )

    total = 0
    for item in carrito:
        total += item["precio"] * item["cantidad"]

    return render_template(
        "carrito.html",
        carrito=carrito,
        total=total
    )

@app.route("/actualizar_carrito/<id>", methods=["POST"])
def actualizar_carrito(id):

    nueva_cantidad = int(request.form["cantidad"])

    carrito_collection.update_one(
        {
            "_id": ObjectId(id),
            "usuario_id": session["user_id"]
        },
        {
            "$set": {"cantidad": nueva_cantidad}
        }
    )

    return redirect(url_for("ver_carrito"))

@app.route("/eliminar_carrito/<id>", methods=["POST"])
def eliminar_carrito(id):

    carrito_collection.delete_one(
        {
            "_id": ObjectId(id),
            "usuario_id": session["user_id"]
        }
    )

    return redirect(url_for("ver_carrito"))

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
    if request.method == "GET":
        return render_template("registro.html")

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

    flash("Registro exitoso", "success")
    return redirect("/login")

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

@app.route("/compra")
def compra():
    if "usuario" not in session:
        return redirect("/login")
    return render_template("compra.html")

@app.route("/adopcion")
def adopcion():
    if "usuario" not in session:
        flash("Debes iniciar sesión para acceder a esta página", "warning")
        return redirect("/login")

    print("a")
    print(dict(session))  

    perros = list(perros_collection.find())

    return render_template("adopcion.html", perros=perros)

@app.route("/articulos")
def articulos():
    if "usuario" not in session:
        return redirect("/login")
    return render_template("articulos.html")

@app.route("/compra")
def compra():
    return render_template("compra.html")


@app.route("/articulos")
def articulos():
    return render_template("articulos.html")


@app.route("/perfil")
def perfil():
    return render_template("perfil.html")

if __name__ == '__main__':
    app.run(debug=True)