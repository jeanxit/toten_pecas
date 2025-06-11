from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import requests
import logging
import re
import json
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "trocar_essa_chave")  # importante para sessão segura

# Configurações da API GLPI
API_URL = "http://192.168.0.243:81/glpi/apirest.php"
APP_TOKEN = os.getenv("GLPI_APP_TOKEN", "L5QfA9vpW8U9NgODAsAIAO0LfGCurcqYJOc9O1S6")

logging.basicConfig(level=logging.INFO)


def limpar_html(texto):
    """Remove tags HTML de uma string."""
    return re.sub(r'<[^>]+>', '', texto or "")


def login_glpi(user, password):
    """Realiza login na API GLPI e retorna o session_token."""
    try:
        logging.info(f"Realizando login na API GLPI para usuário {user}")
        response = requests.post(
            f"{API_URL}/initSession",
            json={"login": user, "password": password},
            headers={"App-Token": APP_TOKEN}
        )
        response.raise_for_status()
        session_token = response.json().get("session_token")
        if not session_token:
            raise ValueError("Token de sessão não recebido.")
        logging.info("Login realizado com sucesso")
        return session_token
    except Exception as e:
        logging.error(f"Erro no login: {e}")
        return None


def logout_glpi(session_token):
    """Finaliza a sessão ativa na API."""
    if session_token:
        try:
            requests.get(
                f"{API_URL}/killSession",
                headers={"App-Token": APP_TOKEN, "Session-Token": session_token}
            )
            logging.info("Logout realizado com sucesso")
        except Exception as e:
            logging.warning(f"Erro ao realizar logout: {e}")


def get_user_id(session_token, usuario_login):
    """Busca o ID do usuário GLPI a partir do login."""
    headers = {"App-Token": APP_TOKEN, "Session-Token": session_token}
    params = {
        "criteria[0][field]": "name",
        "criteria[0][value]": usuario_login,
        "criteria[0][searchtype]": "equals"
    }
    try:
        r = requests.get(f"{API_URL}/User", headers=headers, params=params)
        r.raise_for_status()
        users = r.json()
        if users:
            return users[0]["id"]
        else:
            logging.warning(f"Usuário GLPI '{usuario_login}' não encontrado")
    except Exception as e:
        logging.error(f"Erro buscando usuário: {e}")
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")
        if not usuario or not senha:
            flash("Usuário e senha são obrigatórios", "error")
            return render_template("login.html")

        token = login_glpi(usuario, senha)
        if not token:
            flash("Credenciais inválidas", "error")
            return render_template("login.html")

        session["session_token"] = token
        session["usuario"] = usuario
        return redirect(url_for("escolha"))

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_api():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "JSON inválido"}), 400

    usuario = dados.get("usuario")
    senha = dados.get("senha")

    if not usuario or not senha:
        return jsonify({"erro": "Usuário e senha são obrigatórios"}), 400

    token = login_glpi(usuario, senha)
    if not token:
        return jsonify({"erro": "Usuário ou senha incorretos."}), 401

    session["session_token"] = token
    session["usuario"] = usuario

    return jsonify({"sucesso": True, "mensagem": "Login realizado com sucesso"})


@app.route("/escolha")
def escolha():
    if "session_token" not in session or "usuario" not in session:
        return redirect(url_for("index"))
    return render_template("escolha.html")


@app.route("/logout")
def logout():
    token = session.get("session_token")
    logout_glpi(token)
    session.clear()
    return redirect(url_for("index"))


@app.route("/resultadoChamados")
def resultado_chamados():
    token = session.get("session_token")
    usuario = session.get("usuario")

    if not token or not usuario:
        return redirect(url_for("index"))

    user_id = get_user_id(token, usuario)
    if not user_id:
        flash("Não foi possível identificar usuário GLPI", "error")
        return redirect(url_for("index"))

    try:
        headers = {"App-Token": APP_TOKEN, "Session-Token": token}
        response = requests.get(f"{API_URL}/Ticket", headers=headers)
        response.raise_for_status()
        tickets = response.json()

        tickets_por_status = {"Aberto": [], "Em Andamento": [], "Finalizado": []}
        status_map = {1: "Aberto", 2: "Em Andamento", 3: "Finalizado", 4: "Finalizado"}

        for t in tickets:
            if t.get("users_id_lastupdater") is None:
                continue

            status = status_map.get(t.get("status"), "Aberto")
            tickets_por_status[status].append({
                "id": t.get("id"),
                "nome": t.get("name"),
                "status": status,
                "descricao": limpar_html(t.get("content", "")),
                "data_criacao": t.get("date"),
                "usuario_id": t.get("users_id_lastupdater")
            })

        return render_template("tickets.html", chamados=tickets_por_status, usuario=usuario)

    except Exception as e:
        logging.error(f"Erro ao buscar chamados: {e}")
        session.clear()
        return redirect(url_for("index"))


@app.route("/meus-chamados")
def meus_chamados():
    token = session.get("session_token")
    usuario = session.get("usuario")

    if not token or not usuario:
        return redirect(url_for("index"))

    user_id = get_user_id(token, usuario)
    if not user_id:
        flash("Não foi possível identificar usuário GLPI", "error")
        return redirect(url_for("index"))

    try:
        headers = {"App-Token": APP_TOKEN, "Session-Token": token}
        params = {
            "criteria[0][field]": "users_id_recipient",
            "criteria[0][value]": user_id,
            "criteria[0][searchtype]": "equals"
        }
        response = requests.get(f"{API_URL}/Ticket", headers=headers, params=params)
        response.raise_for_status()
        tickets = response.json()

        tickets_por_status = {"Aberto": [], "Em Andamento": [], "Finalizado": []}
        status_map = {1: "Aberto", 2: "Em Andamento", 3: "Finalizado", 4: "Finalizado"}

        for t in tickets:
            if t.get("users_id_lastupdater") is None:
                continue

            status = status_map.get(t.get("status"), "Aberto")
            tickets_por_status[status].append({
                "id": t.get("id"),
                "nome": t.get("name"),
                "status": status,
                "descricao": limpar_html(t.get("content", "")),
                "data_criacao": t.get("date"),
                "usuario_id": t.get("users_id_lastupdater")
            })

        return render_template("tickets.html", chamados=tickets_por_status, usuario=usuario)

    except Exception as e:
        logging.error(f"Erro ao buscar chamados: {e}")
        session.clear()
        return redirect(url_for("index"))


@app.route("/novo-chamado", methods=["GET", "POST"])
def criar_chamado():
    token = session.get("session_token")
    usuario = session.get("usuario")

    if not token or not usuario:
        return redirect(url_for("index"))

    headers = {"App-Token": APP_TOKEN, "Session-Token": token}

    def fetch_paginated_data(endpoint):
        start = 0
        limit = 100
        results = []
        while True:
            try:
                resp = requests.get(
                    f"{API_URL}/{endpoint}",
                    headers=headers,
                    params={"range": f"{start}-{start + limit - 1}"}
                )
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                results.extend(data)
                if len(data) < limit:
                    break
                start += limit
            except Exception as e:
                logging.error(f"Erro ao buscar dados de {endpoint}: {e}")
                break
        return results

    usuarios_raw = fetch_paginated_data("User")
    categorias_raw = fetch_paginated_data("ITILCategory")
    setores_raw = fetch_paginated_data("Group")

    logging.debug(f"Usuarios raw: {usuarios_raw}")
    logging.debug(f"Categorias raw: {categorias_raw}")
    logging.debug(f"Setores raw: {setores_raw}")

    observadores_lista = []
    for user in usuarios_raw:
        login = user.get("name", "")
        nome_formatado = login
        if "." in login:
            partes = login.split(".")
            if len(partes) == 2:
                nome_formatado = f"{partes[1].capitalize()} {partes[0].capitalize()}"
        observadores_lista.append({
            "value": login,
            "name": nome_formatado
        })

    categorias = [
        {"id": cat.get("id"), "nome": cat.get("completename") or cat.get("name") or "Sem nome"}
        for cat in categorias_raw
    ]

    setores = [
        {"id": grupo.get("id"), "nome": grupo.get("name") or "Sem nome"}
        for grupo in setores_raw
    ]

    tipos = ["Incidente", "Requisição"]
    urgencias = ["Baixa", "Média", "Alta"]

    # Valores selecionados para manter após POST
    selecionados = {
        "tipo": None,
        "categoria": None,
        "urgencia": None,
        "setor_solicitante": None,
        "observadores_raw": None,
        "nome": None,
        "descricao": None,
    }

    if request.method == "POST":
        tipo = request.form.get("tipo")
        categoria = request.form.get("categoria")
        urgencia = request.form.get("urgencia")
        observadores_raw = request.form.get("observadores")
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        setor_solicitante = request.form.get("setor_solicitante")
        arquivos = request.files.getlist("arquivo")  # Ainda não usado

        # Atualiza valores selecionados para renderizar no template
        selecionados.update({
            "tipo": tipo,
            "categoria": categoria,
            "urgencia": urgencia,
            "setor_solicitante": setor_solicitante,
            "observadores_raw": observadores_raw,
            "nome": nome,
            "descricao": descricao,
        })

        # Validação campos obrigatórios
        if not all([nome, descricao, setor_solicitante, tipo]):
            flash("Campos obrigatórios não preenchidos.", "error")
            return render_template(
                "criar_chamado.html",
                observadores_lista=observadores_lista,
                categorias=categorias,
                setores=setores,
                tipos=tipos,
                urgencias=urgencias,
                selecionados=selecionados
            )

        if tipo not in tipos:
            flash("Tipo inválido.", "error")
            return render_template(
                "criar_chamado.html",
                observadores_lista=observadores_lista,
                categorias=categorias,
                setores=setores,
                tipos=tipos,
                urgencias=urgencias,
                selecionados=selecionados
            )

        try:
            categoria_id = int(categoria)
        except (ValueError, TypeError):
            categoria_id = None

        try:
            setor_solicitante_id = int(setor_solicitante)
        except (ValueError, TypeError):
            flash("Setor solicitante inválido.", "error")
            return render_template(
                "criar_chamado.html",
                observadores_lista=observadores_lista,
                categorias=categorias,
                setores=setores,
                tipos=tipos,
                urgencias=urgencias,
                selecionados=selecionados
            )

        urgencia_map = {"Baixa": 1, "Média": 2, "Alta": 3}
        urgencia_val = urgencia_map.get(urgencia, 2)

        observadores_ids = []
        try:
            if observadores_raw:
                obs_json = json.loads(observadores_raw)
                for item in obs_json:
                    login = item.get("value")
                    match = next((u for u in usuarios_raw if u.get("name") == login), None)
                    if match:
                        observadores_ids.append(match.get("id"))
        except Exception as e:
            logging.error(f"Erro nos observadores: {e}")
            flash("Erro ao processar os observadores.", "error")

        payload = {
            "input": {
                "name": nome,
                "content": descricao,
                "status": 1,
                "type": 1 if tipo == "Incidente" else 2,
                "urgency": urgencia_val,
                "itilcategories_id": categoria_id,
                "users_id_observer": observadores_ids,
                "groups_id_requester": setor_solicitante_id
            }
        }

        try:
            headers.update({"Content-Type": "application/json"})
            response = requests.post(f"{API_URL}/Ticket", headers=headers, json=payload)
            response.raise_for_status()
            ticket_id = response.json().get("id")
            if ticket_id:
                flash(f"Chamado criado com sucesso! ID: {ticket_id}", "success")
                return redirect(url_for("resultado_chamados"))
            else:
                flash("Erro ao criar chamado: resposta inesperada.", "error")
        except Exception as e:
            logging.error(f"Erro ao criar chamado: {e}")
            flash("Erro ao criar chamado. Tente novamente mais tarde.", "error")

    return render_template(
        "criar_chamado.html",
        observadores_lista=observadores_lista,
        categorias=categorias,
        setores=setores,
        tipos=tipos,
        urgencias=urgencias,
        selecionados=selecionados
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
