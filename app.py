import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

DATABASE_URL = os.environ.get('DATABASE_URL')
PDF_FOLDER = 'RATs_Gerados'
MODELO_PDF = 'modelo_rat.pdf'

USUARIOS_PERMITIDOS = ['tecsenior', 'tecnicon2', 'tecnicon1']
PASSWORD_ADMIN = 'S@cCham@d##s2005'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS chamados (
            id SERIAL PRIMARY KEY,
            codigo_os TEXT,
            cliente TEXT,
            empresa TEXT,
            whatsapp TEXT,
            descricao TEXT,
            status TEXT DEFAULT 'Aberto',
            tecnico_responsavel TEXT DEFAULT 'Nenhum',
            urgencia TEXT DEFAULT 'Média',
            data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- COPIE ABAIXO TODAS AS SUAS ROTAS ANTIGAS ---
# Exemplo de como ajustar a rota 'admin' para o Postgres:
@app.route('/admin')
def admin():
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    # Usamos RealDictCursor para o código funcionar como se fosse sqlite3.Row
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM chamados WHERE status != 'Finalizado' ORDER BY id DESC")
    chamados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', chamados=chamados)

# Adicione aqui todas as outras rotas (@app.route('/arquivados'), /detalhes, /finalizar, etc.)
# Lembre-se de substituir o bloco "with sqlite3.connect(DB_PATH) as conn:" 
# pela estrutura:
# conn = get_db_connection()
# cur = conn.cursor(cursor_factory=RealDictCursor)
# ... código ...
# conn.commit()
# cur.close()
# conn.close()

if __name__ == '__main__':
    app.run()
