from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_epn_2026"

# ── Conexión ──────────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host="mysql_principal",
        user="root",
        password="root",
        database="tareas_db",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        use_unicode=True
    )

# ── CRUD: Estudiantes ─────────────────────────────────────────
def buscar_estudiante(cedula, password):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT id, nombre FROM estudiantes WHERE cedula=%s AND password=%s",
        (cedula, password)
    )
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

# ── CRUD: Tareas ──────────────────────────────────────────────
def obtener_tareas(estudiante_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT t.id, t.codigo, t.titulo, t.descripcion, t.fecha_limite,
               e.id AS entrega_id, e.respuesta, e.fecha_entrega
        FROM tareas t
        LEFT JOIN entregas e
               ON e.tarea_id = t.id AND e.estudiante_id = %s
        ORDER BY t.fecha_limite ASC
    """, (estudiante_id,))
    tareas = cur.fetchall()
    cur.close(); db.close()
    return tareas

def obtener_tarea(tarea_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tareas WHERE id=%s", (tarea_id,))
    tarea = cur.fetchone()
    cur.close(); db.close()
    return tarea

# ── CRUD: Entregas ────────────────────────────────────────────
def buscar_entrega(tarea_id, estudiante_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM entregas WHERE tarea_id=%s AND estudiante_id=%s",
        (tarea_id, estudiante_id)
    )
    entrega = cur.fetchone()
    cur.close(); db.close()
    return entrega

def guardar_entrega(tarea_id, estudiante_id, respuesta):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO entregas (tarea_id, estudiante_id, respuesta, fecha_entrega) VALUES (%s,%s,%s,%s)",
        (tarea_id, estudiante_id, respuesta, datetime.now())
    )
    db.commit()
    cur.close(); db.close()

def obtener_mis_entregas(estudiante_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT t.codigo, t.titulo, e.respuesta, e.fecha_entrega
        FROM entregas e JOIN tareas t ON t.id = e.tarea_id
        WHERE e.estudiante_id = %s
        ORDER BY e.fecha_entrega DESC
    """, (estudiante_id,))
    entregas = cur.fetchall()
    cur.close(); db.close()
    return entregas

# ── Rutas ─────────────────────────────────────────────────────
@app.route("/")
def index():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("tareas"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        cedula   = request.form["cedula"]
        password = request.form["password"]
        est = buscar_estudiante(cedula, password)
        if est:
            session["estudiante_id"]     = est["id"]
            session["estudiante_nombre"] = est["nombre"]
            return redirect(url_for("tareas"))
        flash("Cédula o contraseña incorrectos", "danger")
    return render_template("login.html", nodo="Servidor 2")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/tareas")
def tareas():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    lista = obtener_tareas(session["estudiante_id"])
    return render_template("tareas.html", tareas=lista,
                           ahora=datetime.now(), nodo="Servidor 2")

@app.route("/entregar/<int:tarea_id>", methods=["GET","POST"])
def entregar(tarea_id):
    if "estudiante_id" not in session:
        return redirect(url_for("login"))

    tarea   = obtener_tarea(tarea_id)
    entrega = buscar_entrega(tarea_id, session["estudiante_id"])
    ahora   = datetime.now()

    if request.method == "POST":
        respuesta = request.form.get("respuesta","").strip()
        if entrega:
            flash("Ya entregaste esta tarea", "warning")
        elif ahora > tarea["fecha_limite"]:
            flash("El plazo de entrega ya venció", "danger")
        elif not respuesta:
            flash("La respuesta no puede estar vacía", "warning")
        else:
            guardar_entrega(tarea_id, session["estudiante_id"], respuesta)
            flash("¡Tarea entregada!", "success")
            return redirect(url_for("tareas"))

    return render_template("entregar.html", tarea=tarea,
                           entrega=entrega, ahora=ahora, nodo="Servidor 2")

@app.route("/mis-entregas")
def mis_entregas():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    entregas = obtener_mis_entregas(session["estudiante_id"])
    return render_template("mis_entregas.html", entregas=entregas, nodo="Servidor 2")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
