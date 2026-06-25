import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, send_file, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

# O Render fornece esta variável automaticamente
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    return f"OS-{''.join(random.choice(caracteres) for _ in range(6))}"

# --- ROTAS ---

@app.route('/')
def index():
    return render_template('cliente.html')

@app.route('/enviar_chamado', methods=['POST'])
def enviar_chamado():
    # Coleta os dados do formulário
    cliente = request.form.get('cliente')
    empresa = request.form.get('empresa')
    whatsapp = request.form.get('whatsapp')
    descricao = request.form.get('descricao')
    urgencia = request.form.get('urgencia', 'Média')
    
    # Salva no banco de dados Postgres
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO chamados (codigo_os, cliente, empresa, whatsapp, descricao, urgencia)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (gerar_codigo_os(), cliente, empresa, whatsapp, descricao, urgencia))
    conn.commit()
    cur.close()
    conn.close()
    
    # Redireciona para uma página de sucesso (ou volta para o cliente.html)
    return "Chamado enviado com sucesso! <a href='/'>Voltar</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('usuario') in ['tecsenior', 'tecnicon2', 'tecnicon1'] and request.form.get('senha') == 'S@cCham@d##s2005':
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

@app.route('/rat_avulsa')
def rat_avulsa():
    if not session.get('logado'): return redirect(url_for('login'))
    return render_template('rat.html', chamado={"id": 0, "codigo_os": gerar_codigo_os()})

@app.route('/chamado/<int:id>/excluir', methods=['POST'])
def excluir_chamado(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chamados WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/modelo_base_pdf') # Mudei aqui para coincidir com o erro do console
def modelo_rat():
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_base, 'modelo_rat.pdf')
    
    if os.path.exists(caminho_arquivo):
        return send_file(caminho_arquivo, mimetype='application/pdf')
    else:
        return "Arquivo não encontrado", 404
        
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

if __name__ == '__main__':
    app.run()
