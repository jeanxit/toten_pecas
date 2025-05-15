from flask import Flask, request, render_template
import pandas as pd
import requests
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"

def consulta_cnpja(cnpj):
    url = f"https://open.cnpja.com/office/{cnpj}"
    headers = {
        "Accept": "application/json"
        # "Authorization": "Bearer SEU_TOKEN_AQUI"  # Adicione seu token se necessário
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"[ERRO] Falha na consulta CNPJA: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    erro = None

    if request.method == "POST":
        cnpjs = []

        # Entrada manual
        cnpj_digitado = request.form.get("cnpj", "").strip()
        if cnpj_digitado:
            cnpjs.append(cnpj_digitado)

        # Arquivo Excel
        file = request.files.get("file")
        if file and file.filename.endswith(".xlsx"):
            try:
                df = pd.read_excel(file, dtype={"CNPJ_CLIFOR": str})
                if "CNPJ_CLIFOR" not in df.columns:
                    erro = "A planilha deve conter a coluna 'CNPJ_CLIFOR'."
                    return render_template("index.html", error=erro)
                cnpjs.extend(df["CNPJ_CLIFOR"].dropna().astype(str).tolist())
            except Exception as e:
                erro = f"Erro ao ler o arquivo: {str(e)}"
                return render_template("index.html", error=erro)

        # Sanitização e validação dos CNPJs
        cnpjs = list(set([c.strip().zfill(14) for c in cnpjs if c.strip().isdigit() and len(c.strip()) <= 14]))

        if not cnpjs:
            erro = "Nenhum CNPJ válido foi informado."
            return render_template("index.html", error=erro)

        print(f"[INFO] Total de CNPJs para consultar: {len(cnpjs)}")

        erros_brasilapi = []

        # === Etapa 1: BrasilAPI ===
        for idx, cnpj in enumerate(cnpjs):
            print(f"[INFO] ({idx+1}/{len(cnpjs)}) Consultando BrasilAPI: {cnpj}")
            try:
                r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
                if r.status_code == 200:
                    dados = r.json()
                    opcao = dados.get("opcao_pelo_simples")
                    resultados.append({
                        "CNPJ": cnpj,
                        "opcao_pelo_simples": opcao if opcao is not None else "não encontrado",
                        "fonte": "BrasilAPI"
                    })
                else:
                    erros_brasilapi.append(cnpj)
            except requests.RequestException as e:
                print(f"[ERRO] BrasilAPI falhou: {e}")
                erros_brasilapi.append(cnpj)

            if idx + 1 < len(cnpjs):
                time.sleep(2)

        # === Etapa 2: Primeira tentativa CNPJA ===
        erros_cnpja = []
        if erros_brasilapi:
            print(f"[INFO] Tentando CNPJA para {len(erros_brasilapi)} CNPJs com erro na BrasilAPI.")
            for idx, cnpj in enumerate(erros_brasilapi):
                print(f"[INFO] ({idx+1}/{len(erros_brasilapi)}) CNPJA: {cnpj}")
                data = consulta_cnpja(cnpj)
                if data:
                    simples = data.get("company", {}).get("simples", {})
                    optante = simples.get("optant", "não encontrado")
                    resultados.append({
                        "CNPJ": cnpj,
                        "opcao_pelo_simples": optante,
                        "fonte": "CNPJA"
                    })
                else:
                    erros_cnpja.append(cnpj)

                if idx + 1 < len(erros_brasilapi):
                    time.sleep(20)

        # === Etapa 3: Segunda tentativa CNPJA ===
        if erros_cnpja:
            print(f"[INFO] Segunda tentativa CNPJA para {len(erros_cnpja)} CNPJs.")
            for idx, cnpj in enumerate(erros_cnpja):
                print(f"[INFO] ({idx+1}/{len(erros_cnpja)}) Segunda tentativa: {cnpj}")
                data = consulta_cnpja(cnpj)
                if data:
                    simples = data.get("company", {}).get("simples", {})
                    optante = simples.get("optant", "não encontrado")
                    resultados.append({
                        "CNPJ": cnpj,
                        "opcao_pelo_simples": optante,
                        "fonte": "CNPJA (2ª tentativa)"
                    })
                else:
                    resultados.append({
                        "CNPJ": cnpj,
                        "opcao_pelo_simples": "erro",
                        "fonte": "CNPJA (2ª tentativa)"
                    })

                if idx + 1 < len(erros_cnpja):
                    time.sleep(20)

        return render_template("index.html", resultados=resultados)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
