from flask import Flask, request, send_file
import pymysql
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
DB_HOST = "sql100.infinityfree.com"
DB_USER = "if0_41314838"
DB_PASS = "Velux454577"
DB_NAME = "if0_41314838_zynera"

AGENT_FILE = "ZyneraAgent.exe"  # met le .exe dans le repo pour simplifier

# ---------------- UTILITAIRES ----------------
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_session(token):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM remote_sessions WHERE token=%s AND expires_at >= NOW()"
            cursor.execute(sql, (token,))
            return cursor.fetchone()
    finally:
        conn.close()

def delete_session(session_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM remote_sessions WHERE id=%s"
            cursor.execute(sql, (session_id,))
        conn.commit()
    finally:
        conn.close()

# ---------------- ENDPOINT ----------------
@app.route("/download", methods=["GET"])
def download_agent():
    token = request.args.get("token")
    if not token:
        return "Erreur : Token manquant.", 400

    session = get_session(token)
    if not session:
        return "Erreur : Token invalide ou expiré.", 403

    if not os.path.exists(AGENT_FILE):
        return "Erreur : Fichier agent introuvable.", 404

    delete_session(session["id"])

    return send_file(
        AGENT_FILE,
        as_attachment=True,
        download_name="ZyneraAgent.exe"
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
