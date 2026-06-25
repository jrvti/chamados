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

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

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

def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    return f"OS-{''.join(random.choice(caracteres) for _ in range(6))}"

# --- ROTAS ---

@app.route('/')
def index():
    return render_template('cliente.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('usuario') in USUARIOS_PERMITIDOS and request.form.get('senha') == PASSWORD_ADMIN:
            session['logado'] = True
            session['usuario'] = request.form.get('usuario')
            return redirect(url_for('admin'))
        return render_template('login.html', erro="Credenciais incorretas.")
    return render_template('login.html', erro=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        cur.execute("UPDATE chamados SET status = %s, tecnico_responsavel = %s, urgencia = %s WHERE id = %s", 
                    (request.form.get('status'), request.form.get('tecnico_responsavel'), request.form.get('urgencia'), request.form.get('id')))
        conn.commit()
    
    busca = request.args.get('busca', '')
    query = "SELECT * FROM chamados WHERE status != 'Finalizado'"
    if busca:
        query += f" AND (codigo_os ILIKE '%{busca}%' OR cliente ILIKE '%{busca}%')"
    cur.execute(query + " ORDER BY id DESC")
    chamados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', chamados=chamados, tecnico_atual=session.get('usuario'), busca=busca)

@app.route('/rat_avulsa')
def rat_avulsa():
    if not session.get('logado'): return redirect(url_for('login'))
    return render_template('rat.html', chamado={"id": 0, "codigo_os": gerar_codigo_os(), "cliente": "", "empresa": "", "whatsapp": "", "descricao": ""})

@app.route('/dashboard')
def dashboard():
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT status, COUNT(*) as qtd FROM chamados GROUP BY status")
    stats = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', stats=stats)

# Adicione as rotas /arquivados, /detalhes, /finalizar e /excluir seguindo o padrão de 
# abrir/fechar conexão com get_db_connection() e usar RealDictCursor.

if __name__ == '__main__':
    app.run()
