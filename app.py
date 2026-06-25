import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

# O Render injeta a URL do banco de dados aqui
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

# Executa ao iniciar
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
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario in USUARIOS_PERMITIDOS and senha == PASSWORD_ADMIN:
            session['logado'] = True
            session['usuario'] = usuario
            return redirect(url_for('admin'))
        return render_template('login.html', erro="Credenciais incorretas.")
    return render_template('login.html', erro=None)

@app.route('/rat_avulsa')
def rat_avulsa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Criamos um "chamado fictício" para que o template 'rat.html' 
    # não dê erro ao tentar exibir os campos
    chamado_ficticio = {
        "id": 0, 
        "codigo_os": gerar_codigo_os(),
        "cliente": "Atendimento Avulso",
        "empresa": "JRV-TI",
        "whatsapp": "",
        "descricao": "Atendimento Técnico sem O.S. vinculada"
    }
    return render_template('rat.html', chamado=chamado_ficticio)

@app.route('/arquivados')
def arquivados():
    if not session.get('logado'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM chamados WHERE status = 'Finalizado' ORDER BY id DESC")
    chamados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('arquivados.html', chamados=chamados)

@app.route('/dashboard')
def dashboard():
    if not session.get('logado'): return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as qtd, status FROM chamados GROUP BY status")
    stats = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', stats=stats)

# Nota: As rotas de finalizar, excluir e rat devem seguir o mesmo padrão:
# 1. Abrir conexão com get_db_connection()
# 2. Usar cursor(cursor_factory=RealDictCursor)
# 3. Fechar cursor e conexão sempre.

if __name__ == '__main__':
    app.run()
