from flask import Flask, request, render_template
import pandas as pd
import requests
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Ainda necessário se quiser usar sessão futuramente

# Variável global para armazenar os resultados temporariamente
RESULTADOS_TEMP = []

@app.route("/", methods=["GET", "POST"])
def index():
    global RESULTADOS_TEMP
    resultados = []
    erro = None

    if request.method == "POST":
        cnpjs = []

        # CNPJ digitado manualmente
        if request.form.get("cnpj"):
            cnpj_digitado = request.form["cnpj"].strip()
            cnpjs.append(cnpj_digitado)

        # Planilha enviada
        file = request.files.get("file")
        if file and file.filename.endswith(".xlsx"):
            try:
                df = pd.read_excel(file, dtype={"CNPJ_CLIFOR": str})
            except Exception as e:
                erro = "Erro ao ler o arquivo. Verifique se a coluna 'CNPJ_CLIFOR' existe e está correta."
                return render_template("index.html", error=erro)

            if "CNPJ_CLIFOR" not in df.columns:
                erro = "A planilha precisa ter a coluna 'CNPJ_CLIFOR'"
                return render_template("index.html", error=erro)

            cnpjs.extend(df["CNPJ_CLIFOR"].dropna().astype(str).tolist())

        # Limpar, normalizar e remover duplicatas
        cnpjs = list(set([c.strip().zfill(14) for c in cnpjs if c.strip()]))

        print(f"[INFO] Total de CNPJs para consultar: {len(cnpjs)}")

        # Consulta individual com pausa de 3 segundos entre cada
        for idx, cnpj in enumerate(cnpjs):
            print(f"[INFO] ({idx+1}/{len(cnpjs)}) Consultando CNPJ: {cnpj}")
            try:
                r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}")
                if r.status_code == 200:
                    dados = r.json()
                    opcao = dados.get("opcao_pelo_simples")
                    if opcao is None:
                        opcao = "não encontrado"
                    resultados.append({"CNPJ": cnpj, "opcao_pelo_simples": opcao})
                else:
                    resultados.append({"CNPJ": cnpj, "opcao_pelo_simples": "erro"})
            except Exception as e:
                resultados.append({"CNPJ": cnpj, "opcao_pelo_simples": "erro"})

            # Espera de 3 segundos entre as consultas
            if idx + 1 < len(cnpjs):
                time.sleep(2)

        # Armazena na variável global para exportação
        RESULTADOS_TEMP = resultados
        return render_template("index.html", resultados=resultados)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=9900)
