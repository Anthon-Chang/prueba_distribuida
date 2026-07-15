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
        database="video_db",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        use_unicode=True
    )

# ── CRUD: Usuarios ────────────────────────────────────────────
def buscar_usuario(cedula, password):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT id, nombre FROM usuarios WHERE cedula=%s AND password=%s",
        (cedula, password)
    )
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

# ── CRUD: Videos ──────────────────────────────────────────────
def obtener_videos():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, codigo, titulo, descripcion, views, likes, shares, fecha_publicacion
        FROM videos
        ORDER BY views DESC
    """)
    videos = cur.fetchall()
    cur.close(); db.close()
    return videos

def obtener_video(video_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT v.id, v.codigo, v.titulo, v.descripcion, v.views, v.likes, v.shares, v.fecha_publicacion,
               COALESCE(c.comments, 0) AS comments
        FROM videos v
        LEFT JOIN (
            SELECT video_id, COUNT(*) AS comments
            FROM comentarios
            GROUP BY video_id
        ) c ON c.video_id = v.id
        WHERE v.id=%s
    """, (video_id,))
    video = cur.fetchone()
    cur.close(); db.close()
    return video

def obtener_video_mas_visto():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT titulo, views FROM videos ORDER BY views DESC LIMIT 1")
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_video_con_mas_likes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT titulo, likes FROM videos ORDER BY likes DESC LIMIT 1")
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_video_mas_comentado():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT v.titulo, COUNT(c.id) AS comentarios
        FROM videos v
        LEFT JOIN comentarios c ON c.video_id = v.id
        GROUP BY v.id
        ORDER BY comentarios DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_usuario_mas_recurrente():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT u.nombre, x.total
        FROM usuarios u
        JOIN (
            SELECT usuario_id, COUNT(*) AS total
            FROM (
                SELECT usuario_id FROM views
                UNION ALL
                SELECT usuario_id FROM likes
                UNION ALL
                SELECT usuario_id FROM comentarios
                UNION ALL
                SELECT usuario_id FROM shares
            ) t
            GROUP BY usuario_id
        ) x ON x.usuario_id = u.id
        ORDER BY x.total DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_hora_mas_interaccion():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT hora, total
        FROM (
            SELECT DATE_FORMAT(fecha, '%%H:00') AS hora, COUNT(*) AS total
            FROM (
                SELECT fecha FROM views
                UNION ALL
                SELECT fecha FROM likes
                UNION ALL
                SELECT fecha FROM comentarios
                UNION ALL
                SELECT fecha FROM shares
            ) t
            GROUP BY hora
        ) x
        ORDER BY total DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_video_mejor_ratio_interaccion():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT v.titulo,
               COALESCE(v.likes, 0) AS likes,
               COALESCE(c.comments, 0) AS comments,
               COALESCE(s.shares, 0) AS shares,
               v.views,
               ((COALESCE(v.likes, 0) + COALESCE(c.comments, 0) + COALESCE(s.shares, 0)) / NULLIF(v.views, 0)) AS ratio
        FROM videos v
        LEFT JOIN (
            SELECT video_id, COUNT(*) AS comments
            FROM comentarios
            GROUP BY video_id
        ) c ON c.video_id = v.id
        LEFT JOIN (
            SELECT video_id, COUNT(*) AS shares
            FROM shares
            GROUP BY video_id
        ) s ON s.video_id = v.id
        ORDER BY ratio DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    if resultado:
        total_interacciones = resultado["likes"] + resultado["comments"] + resultado["shares"]
        resultado["ratio_text"] = f"likes + comments + shares = {total_interacciones} / {resultado['views']}"
    return resultado

def obtener_estadisticas():
    return {
        "video_mas_visto": obtener_video_mas_visto(),
        "video_mas_likeado": obtener_video_con_mas_likes(),
        "video_mas_comentado": obtener_video_mas_comentado(),
        "usuario_mas_recurrente": obtener_usuario_mas_recurrente(),
        "hora_mas_interaccion": obtener_hora_mas_interaccion(),
        "video_mejor_ratio": obtener_video_mejor_ratio_interaccion()
    }

# ── Rutas ─────────────────────────────────────────────────────
@app.route("/")
def index():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("home"))

@app.route("/home")
def home():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))

    videos = obtener_videos()
    estadisticas = obtener_estadisticas()
    return render_template(
        "home.html",
        videos=videos,
        estadisticas=estadisticas,
        estudiante_nombre=session.get("estudiante_nombre"),
        ahora=datetime.now(),
        nodo="Video Analytics"
    )

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        cedula = request.form["cedula"]
        password = request.form["password"]
        usuario = buscar_usuario(cedula, password)
        if usuario:
            session["estudiante_id"] = usuario["id"]
            session["estudiante_nombre"] = usuario["nombre"]
            return redirect(url_for("home"))
        flash("Cédula o contraseña incorrectos", "danger")
    return render_template("login.html", nodo="Video Analytics")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/videos")
def videos():
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    lista = obtener_videos()
    return render_template("videos.html", videos=lista,
                           ahora=datetime.now(), nodo="Video Analytics")

@app.route("/video/<int:video_id>")
def video(video_id):
    if "estudiante_id" not in session:
        return redirect(url_for("login"))
    video = obtener_video(video_id)
    if not video:
        flash("Video no encontrado", "warning")
        return redirect(url_for("videos"))
    video["ratio"] = None
    if video["views"]:
        video["ratio"] = (
            (video.get("likes", 0) + video.get("comments", 0) + video.get("shares", 0)) / video["views"]
            if video["views"] else None
        )
    return render_template("video.html", video=video, nodo="Video Analytics")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
