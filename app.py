from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import mysql.connector
import requests
from config import mysql_config
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import secrets
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)

conn = mysql.connector.connect(**mysql_config)
cursor = conn.cursor()

# Variável global para armazenar os produtos disponíveis
produtos_disponiveis = {}

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')
@app.route('/register')
def register_page():
    return render_template('registrar.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    senha = request.form['senha']
    remember = 'remember' in request.form

    cursor.execute("SELECT id, nome, senha FROM usuarios WHERE email = %s", (email,))
    resultado = cursor.fetchone()

    if resultado:
        usuario_id, nome_db, senha_hash_db = resultado
        if check_password_hash(senha_hash_db, senha):
            session['nome'] = nome_db
            session['usuario_id'] = usuario_id  # SALVA O ID DO USUÁRIO NA SESSÃO

            if f'carrinho_{nome_db}' not in session:
                session[f'carrinho_{nome_db}'] = []

            flash('Login bem-sucedido!', 'success')

            resp = redirect(url_for('filtro'))
            if remember:
                resp.set_cookie('nome', nome_db, max_age=int(timedelta(days=30).total_seconds()))
                resp.set_cookie('email', email, max_age=int(timedelta(days=30).total_seconds()))
            return resp
        else:
            flash('Senha incorreta!', 'danger')
    else:
        flash('Usuário não encontrado!', 'danger')

    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    senha_hash = generate_password_hash(senha)

    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    if cursor.fetchone():
        flash('Email já registrado! Tente logar.', 'warning')
        return redirect(url_for('index'))

    cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha_hash))
    conn.commit()
    flash('Registro bem-sucedido! Agora faça login.', 'success')
    return redirect(url_for('index'))
@app.route('/logout', methods=['POST'])
def logout():
    # Limpa a sessão inteira
    session.clear()

    # Feedback ao usuário
    flash('Você saiu da conta com sucesso.', 'info')

    # Redireciona para a página inicial
    return redirect(url_for('index'))
# ==================== LOJA ====================
@app.route('/filtro')
def filtro():
    return render_template('filtroPoslogin.html')
@app.route('/buscaCategoria.html')
def busca_categoria():
    return render_template('buscaCategoria.html')
def format_currency(value):
    try:
        value = float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

app.jinja_env.filters['currency'] = format_currency

@app.route('/loja')
def loja():
    nome = session.get('nome') or request.cookies.get('nome')
    if not nome:
        return redirect(url_for('login'))  # Redireciona se não estiver logado

    url = "https://www.zohoapis.com/creator/custom/grupoaiz/Pe_asAPI?publickey=ySdkEmJZO9qMu8pgrMm6FkxYY"
    try:
        response = requests.get(url)
        data = response.json()
        produtos_api = data.get('result', {}).get('Produtos', [])

        produtos_formatados = []
        for produto in produtos_api:
            preco = produto.get('PrecoVenda', '0')
            preco = preco if preco != '-' and preco else '0'
            try:
                preco_float = float(str(preco).replace(',', '.'))
            except ValueError:
                preco_float = 0.0

            imagem_raw = produto.get('Imagem', 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg')  # fallback padrão
            if imagem_raw:
                urls = re.findall(r'https://[^\s"<>]+', imagem_raw)
                if urls:
                    imagem_url = urls[0]  # Usa a primeira URL encontrada
                else:
                    imagem_url = 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg'  # fallback
            else:
                imagem_url = 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg'  # fallback

            produto_formatado = {
            'CodigoProduto': produto.get('CodigoProduto'),
            'Descricao': produto.get('Descricao'),
            'PrecoVenda': preco_float,
            'Imagem': imagem_url,
            'Fabricante': produto.get('Fabricante', '-'),
            'ComprimentoCM': produto.get('ComprimentoCM', '-'),
            'PesoCM': produto.get('PesoCM', '-'),
            'QuantidadeEstoque': produto.get('QuantidadeEstoque', '-')
        }

            produtos_formatados.append(produto_formatado)

        # Armazena os produtos na variável global
        global produtos_disponiveis
        produtos_disponiveis = {produto['CodigoProduto']: produto for produto in produtos_formatados}

        return render_template('loja.html', nome=nome, produtos=produtos_formatados)

    except Exception as e:
        flash(f"Erro ao buscar produtos da API: {e}", "danger")
        return render_template('loja.html', nome=nome, produtos=[])
    
# ==================== CARRINHO ====================
@app.route('/adicionar', methods=['POST'])
def adicionar_carrinho():
    nome = session.get('nome')
    if not nome:
        return redirect(url_for('index'))  # Se não estiver logado, redireciona para a página inicial

    carrinho_nome = f'carrinho_{nome}'

    CodigoProduto = request.form.get('CodigoProduto')

    # Lógica para buscar o produto na variável global
    produto = produtos_disponiveis.get(CodigoProduto)

    if not produto:
        flash(f"Produto com código {CodigoProduto} não encontrado!", "danger")
        return redirect(url_for('loja'))

    # Inicializa o carrinho, se necessário
    if carrinho_nome not in session:
        session[carrinho_nome] = []

    # Verifica se o produto já está no carrinho
    produto_existente = next((item for item in session[carrinho_nome] if item['CodigoProduto'] == CodigoProduto), None)

    if produto_existente:
        produto_existente['quantidade'] += 1  # Incrementa a quantidade do produto no carrinho
        flash(f"Quantidade do produto {produto['Descricao']} aumentada!", "success")
    else:
        # Tratamento da imagem igual ao da loja
        imagem_raw = produto.get('Imagem', 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg')
        if imagem_raw:
            urls = re.findall(r'https://[^\s"<>]+', imagem_raw)
            imagem_url = urls[0] if urls else 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg'
        else:
            imagem_url = 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg'

        preco = max(0, round(produto['PrecoVenda'], 2))
        session[carrinho_nome].append({
            'nome': produto['Descricao'],
            'preco': preco,
            'CodigoProduto': CodigoProduto,
            'quantidade': 1,
            'Imagem': imagem_url  # adiciona imagem já tratada
        })
        flash(f"Produto {produto['Descricao']} adicionado ao carrinho", "success")

    session.modified = True  # Garante que a sessão será salva corretamente
    return redirect(url_for('carrinho'))


@app.route('/carrinho')
def carrinho():
    nome = session.get('nome')
    if not nome:
        return redirect(url_for('index'))

    carrinho_produtos = session.get(f'carrinho_{nome}', [])
    if not carrinho_produtos:
        flash("Seu carrinho está vazio!", "warning")

    for produto in carrinho_produtos:
        imagem_raw = produto.get('Imagem', 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg')
        urls = re.findall(r'https://[^\s"<>]+', imagem_raw)
        produto['Imagem'] = urls[0] if urls else 'https://www.aizparts.com.br/uploads/679a2e3e28c07.jpg'

    return render_template('carrinho.html', produtos=carrinho_produtos)

@app.route('/finalizar-compra', methods=['POST'])
def finalizar_compra():
    nome_usuario = session.get('nome')
    usuario_id = session.get('usuario_id')

    # Verifica se o usuário está logado
    if not nome_usuario or not usuario_id:
        flash('Você precisa estar logado para finalizar a compra.', 'warning')
        return redirect(url_for('index'))

    # Recupera o carrinho do usuário
    carrinho_nome = f'carrinho_{nome_usuario}'
    carrinho = session.get(carrinho_nome, [])

    # Verifica se o carrinho está vazio
    if not carrinho:
        flash('O carrinho está vazio!', 'warning')
        return redirect(url_for('loja'))

    try:
        # Verificando a conexão com o banco de dados
        if conn.is_connected():
            print("Conexão com o banco de dados estabelecida.")
        else:
            raise Exception("Conexão com o banco de dados falhou.")

        # Obtendo o cursor da conexão
        cursor = conn.cursor()

        for item in carrinho:
            codigo = item['CodigoProduto']
            quantidade = item.get('quantidade', 1)  # Pegando a quantidade, se não definida, será 1
            preco = item['preco']
            total = preco * quantidade  # Aqui é onde o total está sendo calculado corretamente

            cursor.execute("""
                INSERT INTO historico_compras (usuario_id, produto_id, quantidade, preco_unitario, total, data_compra, status)
                VALUES (%s, %s, %s, %s, %s, NOW(), 'pendente')
            """, (usuario_id, codigo, quantidade, preco, total))  # Aqui o total é passado corretamente

        # Commit para garantir que as alterações sejam persistidas no banco
        conn.commit()

        # Limpar o carrinho da sessão após a compra
        session[carrinho_nome] = []
        session.modified = True

        # Armazenar flag para mostrar um toast na página index
        session['compra_realizada'] = True
        return redirect(url_for('index'))

    except Exception as e:
        # Em caso de erro, realizar o rollback da transação
        conn.rollback()
        print(f"Erro ao finalizar compra: {e}")
        flash(f"Erro ao finalizar compra: {e}", "danger")
        return redirect(url_for('carrinho'))

    finally:
        cursor.close()
@app.route('/limpar-flag', methods=['POST'])
def limpar_flag():
    session.pop('compra_realizada', None)
    session.modified = True
    return '', 204


# ==================== EMAIL ====================

def enviar_email(destinatario, assunto, corpo_html):
    EMAIL_REMETENTE = 'jean.valdan.2007@gmail.com'
    SENHA_APP = 'ysmfjhbamokvsugi'

    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg.set_content("Use um cliente de e-mail que suporte HTML.")
    msg.add_alternative(corpo_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.send_message(msg)
        flash('E-mail enviado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao enviar o e-mail: {e}', 'danger')

# ==================== RECUPERAÇÃO DE SENHA ====================

@app.route('/esqueceu-senha', methods=['GET', 'POST'])
def esqueceu_senha():
    if request.method == 'POST':
        email = request.form['email']
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if usuario:
            # Gerar token de redefinição e link para redefinição
            token = secrets.token_urlsafe(32)
            expiracao = datetime.now() + timedelta(hours=1)
            cursor.execute("UPDATE usuarios SET token_redefinicao = %s, token_expira = %s WHERE email = %s", (token, expiracao, email))
            conn.commit()

            # Gerar o link e enviar e-mail
            link = f"http://192.168.1.10:5001/nova-senha/{token}"
            corpo_html = f"""
            <html><body>
            <p><a href='{link}'>Clique aqui para redefinir sua senha</a></p>
            <p>Se não foi você, ignore este e-mail.</p>
            </body></html>
            """
            enviar_email(email, "Redefinição de Senha", corpo_html)

            # Flash de sucesso e redirecionamento
            flash('Instruções de recuperação de senha enviadas para o seu e-mail. Verifique sua caixa de entrada ou spam.', 'success')
            return redirect(url_for('login'))  # Redireciona para a página de login após enviar o email
        else:
            flash('E-mail não encontrado!', 'danger')

    return render_template('esqueceu_senha.html')


# ==================== EXECUTAR ====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9901, debug=True)
