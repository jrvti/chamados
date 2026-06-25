from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify
import sqlite3
import os
import random
import string

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

DB_PATH = 'database.db'
PDF_FOLDER = 'RATs_Gerados'
MODELO_PDF = 'modelo_rat.pdf'  # O nome exato do seu arquivo na raiz do projeto

USUARIOS_PERMITIDOS = ['tecsenior', 'tecnicon2', 'tecnicon1']
PASSWORD_ADMIN = 'S@cCham@d##s2005'

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choice(caracteres) for _ in range(6))
    return f"OS-{codigo}"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_os TEXT,
                cliente TEXT,
                empresa TEXT,
                whatsapp TEXT,
                descricao TEXT,
                status TEXT DEFAULT 'Aberto',
                tecnico_responsavel TEXT DEFAULT 'Nenhum',
                urgencia TEXT DEFAULT 'Média',
                data_abertura DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

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

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chamados (codigo_os, cliente, empresa, whatsapp, descricao) 
            VALUES (?, ?, ?, ?, ?)
        ''', (codigo_os, cliente, empresa, whatsapp, descricao_formatada))
        conn.commit()

    # Layout de sucesso totalmente estilizado no padrão visual da JRV-TI
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Chamado Confirmado - JRV-TI</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; padding: 100px 20px; margin: 0; }}
            .container {{ max-width: 480px; background: white; padding: 35px; margin: auto; border: 2px solid #000000; text-align: center; box-shadow: 5px 5px 0px #000000; }}
            h2 {{ color: #000000; margin-top: 0; text-transform: uppercase; border-bottom: 2px solid #000000; padding-bottom: 10px; }}
            p {{ font-size: 16px; color: #333; line-height: 1.6; }}
            .os-box {{ font-size: 24px; background: #000; color: #fff; padding: 12px; margin: 20px 0; font-weight: bold; letter-spacing: 2px; }}
            .btn-voltar {{ display: inline-block; background: #000000; color: white; padding: 12px 25px; border: none; text-decoration: none; margin-top: 15px; font-size: 14px; font-weight: bold; text-transform: uppercase; border: 2px solid #000; }}
            .btn-voltar:hover {{ background: #ffffff; color: #000000; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Chamado Enviado!</h2>
            <p>Seu chamado foi registrado com sucesso em nossa plataforma de triagem técnica.</p>
            <div class="os-box">{codigo_os}</div>
            <p>Guarde e acompanhe o número da sua O.S. acima.</p>
            <a href="/" class="btn-voltar">Voltar ao Início</a>
        </div>
    </body>
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
        else:
            return render_template('login.html', erro="Credenciais incorretas ou usuário inválido.")
            
    return render_template('login.html', erro=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if request.method == 'POST':
            chamado_id = request.form.get('id')
            novo_status = request.form.get('status')
            novo_tecnico = request.form.get('tecnico_responsavel')
            nova_urgencia = request.form.get('urgencia') # Captura a urgência alterada
            
            if novo_status and novo_tecnico and nova_urgencia:
                cursor.execute('''
                    UPDATE chamados 
                    SET status = ?, tecnico_responsavel = ?, urgencia = ? 
                    WHERE id = ?
                ''', (novo_status, novo_tecnico, nova_urgencia, chamado_id))
            elif request.form.get('status') == 'Em Atendimento' and request.form.get('tecnico_responsavel'):
                cursor.execute('''
                    UPDATE chamados 
                    SET status = ?, tecnico_responsavel = ? 
                    WHERE id = ?
                ''', ('Em Atendimento', novo_tecnico, chamado_id))
            conn.commit()
            
        busca = request.args.get('busca', '').strip()
        if busca:
            cursor.execute('''
                SELECT * FROM chamados 
                WHERE status != 'Finalizado' 
                AND (codigo_os LIKE ? OR cliente LIKE ? OR empresa LIKE ? OR descricao LIKE ?)
                ORDER BY id DESC
            ''', (f'%{busca}%', f'%{busca}%', f'%{busca}%', f'%{busca}%'))
        else:
            cursor.execute("SELECT * FROM chamados WHERE status != 'Finalizado' ORDER BY id DESC")
            
        chamados = cursor.fetchall()
        
    return render_template('admin.html', chamados=chamados, tecnico_atual=session.get('usuario'), busca=busca)

@app.route('/arquivados')
def arquivados():
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    busca = request.args.get('busca', '').strip()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if busca:
            cursor.execute('''
                SELECT * FROM chamados 
                WHERE status = 'Finalizado' 
                AND (codigo_os LIKE ? OR cliente LIKE ? OR empresa LIKE ? )
                ORDER BY id DESC
            ''', (f'%{busca}%', f'%{busca}%', f'%{busca}%'))
        else:
            cursor.execute("SELECT * FROM chamados WHERE status = 'Finalizado' ORDER BY id DESC")
        chamados = cursor.fetchall()
        
    return render_template('arquivados.html', chamados=chamados, busca=busca)

@app.route('/chamado/<int:id>/detalhes')
def detalhes(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE id = ?", (id,))
        chamado = cursor.fetchone()
    if chamado:
        return render_template('detalhes.html', chamado=chamado)
    return "Chamado não encontrado.", 404

@app.route('/chamado/<int:id>/rat')
def abrir_rat(id):
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE id = ?", (id,))
        chamado = cursor.fetchone()
        
    if chamado:
        if chamado['status'] == 'Finalizado':
            pdf_salvo = f"{PDF_FOLDER}/RAT_{chamado['codigo_os']}.pdf"
            if os.path.exists(pdf_salvo):
                return send_file(pdf_salvo, as_attachment=True)
            return "Arquivo PDF físico não encontrado no servidor.", 404
        return render_template('rat.html', chamado=chamado)
    return "Chamado não encontrado.", 404

# --- ROTA DA RAT AVULSA (SEM CHAMADO VINCULADO) ---
@app.route('/rat_avulsa')
def rat_avulsa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Criamos um chamado estruturado em formato de dicionário "limpo" 
    # para passar ao template 'rat.html' sem estourar erros de Jinja2
    chamado_ficticio = {
        "id": 0,  # ID 0 indica no salvar que se trata de uma RAT Avulsa
        "codigo_os": gerar_codigo_os(),
        "cliente": "",
        "empresa": "",
        "whatsapp": "",
        "descricao": "Atendimento Técnico Avulso (Sem O.S. prévia)"
    }
    return render_template('rat.html', chamado=chamado_ficticio)

@app.route('/chamado/<int:id>/finalizar', methods=['POST'])
def finalizar_chamado(id):
    if not session.get('logado'):
        return jsonify({"success": False, "error": "Não autenticado"}), 403
        
    if 'pdf_rat' not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
        
    arquivo_pdf = request.files['pdf_rat']
    
    # Se o ID for 0, é uma RAT Avulsa que não possui registro de ID no Banco de dados
    if id == 0:
        # Pega o código da O.S temporária enviado via parâmetro ou gera um alternativo
        codigo_temporario = request.form.get('codigo_os', gerar_codigo_os().replace("OS-", ""))
        pdf_filename = f"{PDF_FOLDER}/RAT_AVULSA_{codigo_temporario}.pdf"
        arquivo_pdf.save(pdf_filename)
        return jsonify({"success": True})
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT codigo_os FROM chamados WHERE id = ?', (id,))
        chamado = cursor.fetchone()
        
        if not chamado:
            return jsonify({"success": False, "error": "Chamado inválido"}), 404

        pdf_filename = f"{PDF_FOLDER}/RAT_{chamado['codigo_os']}.pdf"
        arquivo_pdf.save(pdf_filename)

        cursor.execute("UPDATE chamados SET status = 'Finalizado' WHERE id = ?", (id,))
        conn.commit()

    return jsonify({"success": True})

@app.route('/chamado/<int:id>/excluir', methods=['POST'])
def excluir_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    retorno_painel = 'arquivados'
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_os, status FROM chamados WHERE id = ?", (id,))
        chamado = cursor.fetchone()
        
        if chamado:
            # Se o chamado excluído era ativo, volta para o /admin em vez de /arquivados
            if chamado['status'] != 'Finalizado':
                retorno_painel = 'admin'
                
            pdf_filename = f"{PDF_FOLDER}/RAT_{chamado['codigo_os']}.pdf"
            if os.path.exists(pdf_filename):
                try:
                    os.remove(pdf_filename)
                except:
                    pass
            cursor.execute("DELETE FROM chamados WHERE id = ?", (id,))
            conn.commit()
            
    return redirect(url_for(retorno_painel))

@app.route('/modelo_base_pdf')
def modelo_base_pdf():
    if os.path.exists(MODELO_PDF):
        return send_file(MODELO_PDF, mimetype='application/pdf')
    return "Modelo base não encontrado na raiz.", 404

# --- DASHBOARD INTEGRADA ---
@app.route('/dashboard')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
        
    tecnico_atual = session.get('usuario')

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Totalizadores Rápidos
        cursor.execute("SELECT COUNT(*) FROM chamados WHERE status != 'Finalizado'")
        total_ativos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Finalizado'")
        total_fechados = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chamados WHERE urgencia IN ('Alta', 'Crítica') AND status != 'Finalizado'")
        total_criticos = cursor.fetchone()[0]

        # 2. Ranking de Desempenho por Técnico (Chamados Concluídos)
        cursor.execute('''
            SELECT tecnico_responsavel, COUNT(*) as qtd 
            FROM chamados 
            WHERE status = 'Finalizado' AND tecnico_responsavel != 'Nenhum'
            GROUP BY tecnico_responsavel 
            ORDER BY qtd DESC
        ''')
        ranking_tecnicos = cursor.fetchall()

        # 3. Top 3 Clientes que mais abrem chamados
        cursor.execute('''
            SELECT empresa, COUNT(*) as qtd 
            FROM chamados 
            GROUP BY empresa 
            ORDER BY qtd DESC 
            LIMIT 3
        ''')
        top_clientes = cursor.fetchall()

        # 4. Distribuição por Urgência Geral
        cursor.execute('''
            SELECT urgencia, COUNT(*) as qtd 
            FROM chamados 
            GROUP BY urgencia
        ''')
        distribuicao_urgencia = cursor.fetchall()

    return render_template('dashboard.html', 
                           tecnico_atual=tecnico_atual,
                           total_ativos=total_ativos,
                           total_fechados=total_fechados,
                           total_criticos=total_criticos,
                           ranking_tecnicos=ranking_tecnicos,
                           top_clientes=top_clientes,
                           distribuicao_urgencia=distribuicao_urgencia)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
