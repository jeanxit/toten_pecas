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

app = Flask(__name__)
app.secret_key = os.urandom(24)

conn = mysql.connector.connect(**mysql_config)
cursor = conn.cursor()

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
        return redirect(url_for('login'))

    ultima_atualizacao = session.get('ultima_atualizacao')
    if isinstance(ultima_atualizacao, str):
        try:
            ultima_atualizacao = datetime.fromisoformat(ultima_atualizacao)
        except ValueError:
            ultima_atualizacao = None

    if ultima_atualizacao:
        ultima_atualizacao = ultima_atualizacao.replace(tzinfo=None)

    if not ultima_atualizacao or datetime.now() - ultima_atualizacao > timedelta(minutes=5):
        url = "https://www.zohoapis.com/creator/custom/grupoaiz/Pe_asAPI?publickey=ySdkEmJZO9qMu8pgrMm6FkxYY"
        try:
            response = requests.get(url)
            data = response.json()
            produtos_api = data.get('result', {}).get('Produtos', [])

            if produtos_api:
                cursor.execute("START TRANSACTION")
                for produto in produtos_api:
                    preco = produto.get('PrecoVenda', '0')
                    preco = preco if preco != '-' and preco else '0'

                    codigo_produto = produto.get('CodigoProduto')
                    descricao = produto.get('Descricao')

                    cursor.execute("SELECT * FROM produtos WHERE CodigoProduto = %s", (codigo_produto,))
                    if cursor.fetchone():
                        cursor.execute("""UPDATE produtos SET Descricao = %s, PrecoVenda = %s WHERE CodigoProduto = %s""", (descricao, preco, codigo_produto))
                    else:
                        cursor.execute("""INSERT INTO produtos (CodigoProduto, Descricao, PrecoVenda) VALUES (%s, %s, %s)""", (codigo_produto, descricao, preco))

                conn.commit()
                session['ultima_atualizacao'] = datetime.now().isoformat()
                flash('Dados da API atualizados com sucesso!', 'success')
            else:
                flash('Nenhum dado encontrado na API.', 'warning')
        except Exception as e:
            flash(f"Erro ao buscar peças: {e}", "danger")

    cursor.execute("SELECT CodigoProduto, Descricao, PrecoVenda FROM produtos")
    produtos_db = cursor.fetchall()
    return render_template('loja.html', nome=nome, produtos=produtos_db)

# ==================== CARRINHO ====================
@app.route('/adicionar/<string:CodigoProduto>', methods=['GET'])
def adicionar_carrinho(CodigoProduto):
    nome = session.get('nome')
    if not nome:
        return redirect(url_for('index'))

    # Consulta o produto pelo CodigoProduto
    cursor.execute("SELECT CodigoProduto, Descricao, PrecoVenda FROM produtos WHERE CodigoProduto = %s", (CodigoProduto,))
    produto = cursor.fetchone()

    if not produto:
        flash(f"Produto com código {CodigoProduto} não encontrado!", "danger")
        return redirect(url_for('loja'))

    carrinho_nome = f'carrinho_{nome}'
    if carrinho_nome not in session:
        session[carrinho_nome] = []

    try:
        preco = float(str(produto[2]).replace(',', '.'))
        preco = max(0, round(preco, 2))
    except (ValueError, TypeError):
        preco = 0.0

    session[carrinho_nome].append({
        'nome': produto[1],
        'preco': preco,
        'CodigoProduto': produto[0]  # Usando o código do produto
    })
    session.modified = True

    flash(f"Produto {produto[1]} adicionado ao carrinho", "success")
    return redirect(url_for('carrinho'))


@app.route('/carrinho')
def carrinho():
    nome = session.get('nome')
    if not nome:
        return redirect(url_for('index'))  # Se não estiver logado, redireciona para a página inicial

    carrinho_produtos = session.get(f'carrinho_{nome}', [])
    if not carrinho_produtos:
        flash("Seu carrinho está vazio!", "warning")

    return render_template('carrinho.html', produtos=carrinho_produtos)


@app.route('/finalizar-compra', methods=['POST'])
def finalizar_compra():
    nome_usuario = session.get('nome')
    usuario_id = session.get('usuario_id')  # Certifique-se de salvar isso na sessão após login

    # Verificar se o usuário está logado
    if not nome_usuario or not usuario_id:
        flash('Você precisa estar logado para finalizar a compra.', 'warning')
        return redirect(url_for('index'))  # Se não estiver logado, redireciona para a página inicial

    # Recuperar o carrinho da sessão
    carrinho_nome = f'carrinho_{nome_usuario}'
    carrinho = session.get(carrinho_nome, [])

    # Verificar se o carrinho está vazio
    if not carrinho:
        flash('O carrinho está vazio!', 'warning')
        return redirect(url_for('loja'))  # Redireciona de volta para a loja se o carrinho estiver vazio

    try:
        if conn.open:
            print("Conexão com o banco de dados estabelecida.")
        else:
            raise Exception("Conexão com o banco de dados falhou.")

        produtos_para_inserir = []
        historico_compras = []

        # Calcular o total para cada produto no carrinho e preparar dados para inserção
        for item in carrinho:
            codigo_produto = item['CodigoProduto']  # Usando CodigoProduto agora
            quantidade = item.get('quantidade', 1)
            preco = item['preco']
            total = preco * quantidade  # Calculando o total

            # Preparar os dados para inserção no carrinho_temporal
            produtos_para_inserir.append((usuario_id, codigo_produto, quantidade, preco))
            # Preparar os dados para inserção no histórico de compras, incluindo o total
            historico_compras.append((usuario_id, codigo_produto, quantidade, preco, total))  

        # Inserir os dados no carrinho_temporal
        if produtos_para_inserir:
            cursor.executemany("""
                INSERT INTO carrinho_temporal (usuario_id, produto_id, quantidade, preco_unitario, data_adicao)
                SELECT %s, p.id, %s, %s, NOW()
                FROM produtos p WHERE p.CodigoProduto = %s
            """, produtos_para_inserir)
            print(f"{len(produtos_para_inserir)} produtos inseridos na tabela carrinho_temporal.")

        # Inserir os dados no historico_compras com o total
        if historico_compras:
            cursor.executemany("""
                INSERT INTO historico_compras (usuario_id, produto_id, quantidade, preco_unitario, total, data_compra, status)
                SELECT %s, p.id, %s, %s, %s, NOW(), 'pendente'
                FROM produtos p WHERE p.CodigoProduto = %s
            """, historico_compras)
            print(f"{len(historico_compras)} produtos inseridos no histórico de compras.")

        # Commit para garantir que os dados foram inseridos no banco
        conn.commit()
        print("Dados inseridos e commit realizado com sucesso.")

        # Limpar o carrinho na sessão após a finalização
        session[carrinho_nome] = []  # Limpa o carrinho na sessão
        session.modified = True  # Marca a sessão como modificada

        # Exibir uma mensagem de sucesso
        flash('✅ Seu pedido foi feito com sucesso!', 'success')
        return redirect(url_for('index'))  # Ou redireciona para uma página de confirmação de compra

    except Exception as e:
        print(f"Erro ao finalizar compra: {e}")
        flash(f"Erro ao finalizar compra: {e}", "danger")
        return redirect(url_for('carrinho'))


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
