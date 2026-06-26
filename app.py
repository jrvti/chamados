import os
import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    return f"OS-{''.join(random.choice(caracteres) for _ in range(6))}"

@app.route('/')
def index():
    return render_template('cliente.html')

@app.route('/enviar_chamado', methods=['POST'])
def enviar_chamado():
    cliente = request.form.get('cliente')
    empresa = request.form.get('empresa')
    whatsapp = request.form.get('whatsapp')
    marca = request.form.get('marca', 'Não informado')
    modelo = request.form.get('modelo', 'Não informado')
    descricao = request.form.get('descricao')
    descricao_final = f"Equipamento: {marca} / {modelo} | Problema: {descricao}"
    codigo_gerado = gerar_codigo_os()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO chamados (codigo_os, cliente, empresa, whatsapp, descricao, urgencia)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (codigo_gerado, cliente, empresa, whatsapp, descricao_final, 'Média'))
    conn.commit()
    cur.close()
    conn.close()
    return render_template('sucesso.html', codigo_os=codigo_gerado)
    
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

@app.route('/chamado/<int:id>')
def detalhes_chamado(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM chamados WHERE id = %s", (id,))
    chamado = cur.fetchone()
    cur.close()
    conn.close()
    if not chamado: return "Chamado não encontrado", 404
    return render_template('detalhes.html', chamado=chamado)

@app.route('/chamado/<int:id>/rat')
def rat_chamado(id):
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM chamados WHERE id = %s", (id,))
    chamado = cur.fetchone()
    cur.close()
    conn.close()
    if not chamado: return "Chamado não encontrado", 404
    return render_template('rat.html', chamado=chamado)

@app.route('/chamado/<int:id>/finalizar', methods=['POST'])
def finalizar_chamado_rat(id):
    if not session.get('logado'): return jsonify({"erro": "Não autorizado"}), 401
    diretorio = os.path.join(os.getcwd(), 'RATs_Gerados')
    os.makedirs(diretorio, exist_ok=True)
    if 'pdf' in request.files:
        arquivo_pdf = request.files['pdf']
        arquivo_pdf.save(os.path.join(diretorio, f'RAT_OS_{id}.pdf'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE chamados SET status = 'Finalizado' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"sucesso": True, "mensagem": "Chamado arquivado com sucesso!"}), 200

@app.route('/baixar_rat/<int:id>')
def baixar_rat(id):
    if not session.get('logado'): return redirect(url_for('login'))
    caminho_arquivo = os.path.join(os.getcwd(), 'RATs_Gerados', f'RAT_OS_{id}.pdf')
    if os.path.exists(caminho_arquivo):
        return send_file(caminho_arquivo, as_attachment=True)
    return "Arquivo PDF não encontrado", 404

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

@app.route('/modelo_base_pdf')
def modelo_rat():
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelo_rat.pdf')
    if os.path.exists(caminho_arquivo):
        return send_file(caminho_arquivo, mimetype='application/pdf')
    return "Arquivo não encontrado", 404

@app.route('/dashboard')
def dashboard():
    if not session.get('logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status != 'Finalizado'")
    total_ativos = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status = 'Finalizado'")
    total_fechados = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status != 'Finalizado' AND urgencia IN ('Alta', 'Crítica')")
    total_criticos = cur.fetchone()['total']
    cur.execute("SELECT tecnico_responsavel, COUNT(*) as qtd FROM chamados WHERE status = 'Finalizado' GROUP BY tecnico_responsavel ORDER BY qtd DESC")
    ranking_tecnicos = cur.fetchall()
    cur.execute("SELECT empresa, COUNT(*) as qtd FROM chamados GROUP BY empresa ORDER BY qtd DESC LIMIT 3")
    top_clientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', total_ativos=total_ativos, total_fechados=total_fechados, total_criticos=total_criticos, ranking_tecnicos=ranking_tecnicos, top_clientes=top_clientes)
        
if __name__ == '__main__':
    app.run()
