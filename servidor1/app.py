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
        database="examenad",
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
    cur.execute("""
        SELECT short AS titulo, COUNT(*) AS views
        FROM redes
        WHERE LOWER(accion) = 'view'
        GROUP BY short
        ORDER BY views DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_video_con_mas_likes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT short AS titulo, COUNT(*) AS likes
        FROM redes
        WHERE LOWER(accion) IN ('like', 'likes')
        GROUP BY short
        ORDER BY likes DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    cur.close(); db.close()
    return resultado

def obtener_video_mas_comentado():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT short AS titulo, COUNT(*) AS comentarios
        FROM redes
        WHERE LOWER(accion) IN ('comment', 'comments')
        GROUP BY short
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
        SELECT usuario AS nombre, COUNT(*) AS total
        FROM redes
        GROUP BY usuario
        ORDER BY total DESC
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
            SELECT CONCAT(SUBSTRING_INDEX(hora, ':', 1), ':00') AS hora, COUNT(*) AS total
            FROM redes
            GROUP BY SUBSTRING_INDEX(hora, ':', 1)
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
        SELECT short AS titulo,
               SUM(CASE WHEN LOWER(accion) IN ('like', 'likes') THEN 1 ELSE 0 END) AS likes,
               SUM(CASE WHEN LOWER(accion) IN ('comment', 'comments') THEN 1 ELSE 0 END) AS comments,
               SUM(CASE WHEN LOWER(accion) IN ('share', 'shares') THEN 1 ELSE 0 END) AS shares,
               SUM(CASE WHEN LOWER(accion) = 'view' THEN 1 ELSE 0 END) AS views,
               (
                   (
                       SUM(CASE WHEN LOWER(accion) IN ('like', 'likes') THEN 1 ELSE 0 END) +
                       SUM(CASE WHEN LOWER(accion) IN ('comment', 'comments') THEN 1 ELSE 0 END) +
                       SUM(CASE WHEN LOWER(accion) IN ('share', 'shares') THEN 1 ELSE 0 END)
                   ) / NULLIF(SUM(CASE WHEN LOWER(accion) = 'view' THEN 1 ELSE 0 END), 0)
               ) AS ratio
        FROM redes
        GROUP BY short
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
    # Acceso sin login: mostrar directamente la página principal
    estadisticas = obtener_estadisticas()
    return render_template("home.html", estadisticas=estadisticas)

@app.route("/home")
def home():
    # Acceso sin login: mostrar estadísticas
    estadisticas = obtener_estadisticas()
    return render_template("home.html", estadisticas=estadisticas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
