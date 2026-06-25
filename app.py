import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

# A URL do Postgres que você configurou nas Variáveis de Ambiente do Render
DATABASE_URL = os.environ.get('DATABASE_URL')
PDF_FOLDER = 'RATs_Gerados'
MODELO_PDF = 'modelo_rat.pdf'

USUARIOS_PERMITIDOS = ['tecsenior', 'tecnicon2', 'tecnicon1']
PASSWORD_ADMIN = 'S@cCham@d##s2005'

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def get_db_connection():
    # Conecta no banco na nuvem do Render
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
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
    cursor.close()
    conn.close()

init_db()

def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choice(caracteres) for _ in range(6))
    return f"OS-{codigo}"

@app.route('/')
def index():
    return render_template('cliente.html')

@app.route('/enviar_chamado', methods=['POST'])
def enviar_chamado():
    cliente = request.form.get('cliente')
    empresa = request.form.get('empresa')
    whatsapp = request.form.get('whatsapp')
    descricao_bruta = request.form.get('descricao')
    marca = request.form.get('marca', '')
    modelo = request.form.get('modelo', '')
    descricao_formatada = f"{descricao_bruta} (Equipamento: {marca} - {modelo})" if marca or modelo else descricao_bruta
    codigo_os = gerar_codigo_os()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chamados (codigo_os, cliente, empresa, whatsapp, descricao) 
        VALUES (%s, %s, %s, %s, %s)
    ''', (codigo_os, cliente, empresa, whatsapp, descricao_formatada))
    conn.commit()
    cursor.close()
    conn.close()

    return f"""
    <html>
        <div style="text-align:center; padding:50px;">
            <h2>Chamado Enviado!</h2>
            <p>O.S: {codigo_os}</p>
            <a href="/">Voltar</a>
        </div>
    </html>
    """

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

@app.route('/admin')
def admin():
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM chamados WHERE status != 'Finalizado' ORDER BY id DESC")
    chamados = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', chamados=chamados)

# ... (Mantenha as outras rotas: arquivados, detalhes, rat, etc., 
# aplicando o mesmo padrão de "get_db_connection" e "cursor.close()")

if __name__ == '__main__':
    app.run(debug=True)
