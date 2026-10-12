import os
import sqlite3
import hashlib
import jwt

from datetime import datetime, timedelta
from flask import Flask, render_template, request


app = Flask(__name__)

# Clave secreta para firmar los tokens JWT.
# En Render configuraremos CLAVE_SECRETA como variable de entorno.
CLAVE_SECRETA = os.environ.get(
    "CLAVE_SECRETA",
    "clave-secreta-compustore"
)

# Ubicación de la base de datos.
# Permite encontrar base.db dentro de la carpeta del proyecto.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, "base.db")


# ========================================
# CONEXIÓN Y CREACIÓN DE LA BASE DE DATOS
# ========================================

def conectar_db():
    return sqlite3.connect(RUTA_DB)


def crear_db():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    # Tabla de productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


crear_db()


# ========================================
# PÁGINA PRINCIPAL
# ========================================

@app.route("/")
def inicio():
    return render_template("index.html")


# ========================================
# REGISTRO DE USUARIOS
# ========================================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":

        usuario = request.form["usuario"]
        email = request.form["email"]
        password = request.form["password"]

        # Mantener el método de hash actual del proyecto.
        password_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        conexion = conectar_db()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (usuario, email, password)
                VALUES (?, ?, ?)
            """, (usuario, email, password_hash))

            conexion.commit()
            return "Cuenta creada correctamente"

        except sqlite3.IntegrityError:
            return "El usuario o el email ya están registrados.", 400

        finally:
            conexion.close()

    return render_template("registro.html")


# ========================================
# INICIO DE SESIÓN Y CREACIÓN DEL JWT
# ========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        datos = request.get_json(silent=True)

        if not datos:
            return {"mensaje": "Datos de inicio de sesión inválidos."}, 400

        usuario = datos.get("usuario")
        password = datos.get("password")

        if not usuario or not password:
            return {"mensaje": "Completá usuario y contraseña."}, 400

        password_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT * FROM usuarios
            WHERE usuario = ? AND password = ?
        """, (usuario, password_hash))

        usuario_encontrado = cursor.fetchone()
        conexion.close()

        if usuario_encontrado:

            token = jwt.encode(
                {
                    "usuario": usuario,
                    "exp": datetime.utcnow() + timedelta(hours=2)
                },
                CLAVE_SECRETA,
                algorithm="HS256"
            )

            return {
                "mensaje": "Inicio de sesión correcto",
                "token": token
            }

        return {
            "mensaje": "Usuario o contraseña incorrectos"
        }, 401

    return render_template("login.html")


# ========================================
# VERIFICACIÓN DEL TOKEN JWT
# ========================================

def verificar_token():
    encabezado = request.headers.get("Authorization")

    if not encabezado:
        return None

    if not encabezado.startswith("Bearer "):
        return None

    token = encabezado.split(" ", 1)[1].strip()

    if not token:
        return None

    try:
        datos = jwt.decode(
            token,
            CLAVE_SECRETA,
            algorithms=["HS256"]
        )

        return datos

    except jwt.InvalidTokenError:
        return None


# ========================================
# PERFIL PROTEGIDO
# ========================================

@app.route("/perfil")
def perfil():
    datos = verificar_token()

    if datos is None:
        return {
            "mensaje": "Acceso denegado. Necesitas un token válido."
        }, 401

    return {
        "mensaje": "Acceso permitido",
        "usuario": datos["usuario"]
    }


# ========================================
# PÁGINA VISUAL DEL PERFIL
# ========================================

@app.route("/perfil_pagina")
def perfil_pagina():
    return render_template("perfil.html")


# ========================================
# PÁGINA PARA AGREGAR PRODUCTOS
# ========================================

@app.route("/productos")
def productos():
    return render_template("productos.html")


# ========================================
# GUARDAR PRODUCTO
# ========================================

@app.route("/guardar_producto", methods=["POST"])
def guardar_producto():

    datos_token = verificar_token()

    if datos_token is None:
        return {
            "mensaje": "Acceso denegado. Necesitas iniciar sesión."
        }, 401

    datos = request.get_json(silent=True)

    if not datos:
        return {"mensaje": "Datos del producto inválidos."}, 400

    nombre = datos.get("nombre")
    categoria = datos.get("categoria")
    precio = datos.get("precio")
    stock = datos.get("stock")

    if nombre is None or categoria is None or precio is None or stock is None:
        return {"mensaje": "Completá todos los campos del producto."}, 400

    try:
        precio = float(precio)
        stock = int(stock)

        if precio < 0 or stock < 0:
            raise ValueError

    except (ValueError, TypeError):
        return {"mensaje": "El precio y el stock deben ser valores válidos."}, 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO productos (nombre, categoria, precio, stock)
            VALUES (?, ?, ?, ?)
        """, (nombre, categoria, precio, stock))

        conexion.commit()

    finally:
        conexion.close()

    return {"mensaje": "Producto guardado correctamente"}


# ========================================
# MOSTRAR PRODUCTOS
# ========================================

@app.route("/productos_lista")
def productos_lista():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()

    conexion.close()

    return render_template(
        "productos_lista.html",
        productos=productos
    )


# ========================================
# ELIMINAR PRODUCTO
# ========================================

@app.route("/eliminar_producto/<int:id>", methods=["DELETE"])
def eliminar_producto(id):

    datos_token = verificar_token()

    if datos_token is None:
        return {
            "mensaje": "Acceso denegado. Necesitas iniciar sesión."
        }, 401

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            DELETE FROM productos
            WHERE id = ?
        """, (id,))

        conexion.commit()

    finally:
        conexion.close()

    return {"mensaje": "Producto eliminado correctamente"}


# ========================================
# ACTUALIZAR PRODUCTO
# ========================================

@app.route("/actualizar_producto/<int:id>", methods=["PUT"])
def actualizar_producto(id):

    datos_token = verificar_token()

    if datos_token is None:
        return {
            "mensaje": "Acceso denegado. Necesitas iniciar sesión."
        }, 401

    datos = request.get_json(silent=True)

    if not datos:
        return {"mensaje": "Datos del producto inválidos."}, 400

    nombre = datos.get("nombre")
    categoria = datos.get("categoria")
    precio = datos.get("precio")
    stock = datos.get("stock")

    if nombre is None or categoria is None or precio is None or stock is None:
        return {"mensaje": "Completá todos los campos del producto."}, 400

    try:
        precio = float(precio)
        stock = int(stock)

        if precio < 0 or stock < 0:
            raise ValueError

    except (ValueError, TypeError):
        return {"mensaje": "El precio y el stock deben ser valores válidos."}, 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, categoria = ?, precio = ?, stock = ?
            WHERE id = ?
        """, (nombre, categoria, precio, stock, id))

        conexion.commit()

    finally:
        conexion.close()

    return {"mensaje": "Producto actualizado correctamente"}


# ========================================
# PÁGINA PARA EDITAR PRODUCTOS
# ========================================

@app.route("/editar_producto/<int:id>")
def editar_producto(id):

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT * FROM productos
        WHERE id = ?
    """, (id,))

    producto = cursor.fetchone()
    conexion.close()

    if producto is None:
        return "Producto no encontrado.", 404

    return render_template(
        "editar_producto.html",
        producto=producto
    )


# ========================================
# EJECUTAR APLICACIÓN
# ========================================

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=puerto,
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )