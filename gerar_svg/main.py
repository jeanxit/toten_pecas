import os
import re
import html
from pathlib import Path
from bs4 import BeautifulSoup

# === Caminhos ===
input_svg_path = Path("I2006478.svg")
output_html_path = Path("output/html.html")
output_html_path.parent.mkdir(parents=True, exist_ok=True)

# === Lê o conteúdo SVG ===
with input_svg_path.open("r", encoding="utf-8") as f:
    svg_content = f.read()

# === Remove a tag <metadata> se existir ===
svg_content = re.sub(r"<metadata>.*?</metadata>", "", svg_content, flags=re.DOTALL)

# === Parse com BeautifulSoup ===
soup = BeautifulSoup(svg_content, "xml")

# === Dicionário código -> quantidade (via LineXX) ===
codigo_para_quantidade = {}
for group in soup.find_all("g", id=re.compile(r"Line\d+")):
    texts = group.find_all("text")
    if len(texts) >= 2:
        codigo = texts[0].text.strip()
        quantidade = texts[-1].text.strip()
        if re.match(r"(CO-)?[A-Z0-9]+", codigo) and quantidade.isdigit():
            codigo_para_quantidade[codigo] = int(quantidade)

# === Mapeia elementos hotspot com código e quantidade ===
produtos = {}
for g in soup.find_all("g", id=re.compile(r"hotspot\.\d+")):
    id_hotspot = g.get("id")
    onmousemove = g.get("onmousemove", "")
    match = re.search(r"ShowToolTip\([^,]+,[^,]+,[\"'&quot;]+(.*?)[\"'&quot;]+\)", onmousemove)
    if match:
        codigo_raw = match.group(1)
        # Tenta encontrar a quantidade com ou sem o prefixo "CO-"
        quantidade = (
            codigo_para_quantidade.get(codigo_raw) or
            codigo_para_quantidade.get(f"CO-{codigo_raw}") or
            codigo_para_quantidade.get(codigo_raw.replace("CO-", "")) or
            0
        )
        produtos[id_hotspot] = {
            "codigo": codigo_raw,
            "quantidade": quantidade
        }

# === Serializa SVG final sem <metadata> ===
svg_str = str(soup.svg)

# === Gera entradas JS ===
def js_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

produtos_js_entries = [
    f'"{k}": {{codigo: "{js_escape(v["codigo"])}", quantidade: {v["quantidade"]}}}'
    for k, v in produtos.items()
]

# === HTML completo ===
html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>SVG Interativo</title>
    <style>
        #svg-container svg {{
            max-width: 1000px;
            width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }}
        .highlight {{
            stroke: orange !important;
            stroke-width: 2 !important;
        }}
        #modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeInBackground 0.3s ease forwards;
        }}
        @keyframes fadeInBackground {{
            from {{ background: rgba(0,0,0,0); }}
            to {{ background: rgba(0,0,0,0.6); }}
        }}
        #modal-content {{
            background: linear-gradient(145deg, #ffffff, #e6e9f0);
            padding: 30px 25px 25px 25px;
            border-radius: 12px;
            max-width: 480px;
            width: 90%;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            position: relative;
            text-align: left;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            transform: scale(0.9);
            opacity: 0;
            animation: scaleUpModal 0.3s ease forwards;
        }}
        @keyframes scaleUpModal {{
            to {{
                transform: scale(1);
                opacity: 1;
            }}
        }}
        #modal-close {{
            position: absolute;
            top: 12px;
            right: 18px;
            width: 32px;
            height: 32px;
            border: none;
            background: #f44336;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 3px 8px rgba(244, 67, 54, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            user-select: none;
        }}
        #modal-close:hover {{
            background-color: #d32f2f;
            box-shadow: 0 6px 14px rgba(211, 47, 47, 0.9);
        }}
        #modal-close:focus {{
            outline: none;
            box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.6);
        }}
        #modal-title {{
            font-weight: 700;
            font-size: 1.6rem;
            margin-bottom: 15px;
            color: #333;
        }}
        #modal-body {{
            font-size: 1rem;
            color: #555;
            line-height: 1.5;
        }}
        code {{
            background: #f0f0f3;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.95rem;
            font-family: 'Source Code Pro', monospace;
            display: block;
            margin-top: 10px;
            color: #222;
            box-shadow: inset 2px 2px 5px #ffffff, inset -2px -2px 5px #d1d9e6;
        }}
    </style>
</head>
<body>

<h2 style="text-align:center;">Clique nas áreas interativas do SVG</h2>

<div id="svg-container">
    {svg_str}
</div>

<!-- Modal -->
<div id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-body">
    <div id="modal-content">
        <button id="modal-close" aria-label="Fechar modal">&times;</button>
        <h3 id="modal-title">Informações da Peça</h3>
        <div id="modal-body">Carregando...</div>
    </div>
</div>

<script>
const produtos = {{
{",\n".join(produtos_js_entries)}
}};

document.addEventListener('DOMContentLoaded', () => {{
    const svg = document.querySelector('#svg-container svg');
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.getElementById('modal-close');

    if (!svg) return;

    modalClose.addEventListener('click', () => {{
        modal.style.display = 'none';
    }});

    window.addEventListener('keydown', e => {{
        if (e.key === 'Escape' && modal.style.display === 'flex') {{
            modal.style.display = 'none';
        }}
    }});

    modal.addEventListener('click', (event) => {{
        if (event.target === modal) {{
            modal.style.display = 'none';
        }}
    }});

    const clickableElements = svg.querySelectorAll('[id^="hotspot."]');
    clickableElements.forEach(el => {{
        el.style.cursor = 'pointer';
        el.addEventListener('click', event => {{
            event.stopPropagation();
            const id = el.id;
            const dados = produtos[id];

            if (dados && dados.codigo) {{
                modalTitle.textContent = `Código da peça: ${{dados.codigo}}`;
                modalBody.innerHTML = `
                    <p><strong>Quantidade:</strong> ${{dados.quantidade}}</p>
                    <p><strong>ID interno:</strong> <code>${{id}}</code></p>
                `;
            }} else {{
                modalTitle.textContent = `ID: ${{id}}`;
                modalBody.innerHTML = `<p>Sem dados cadastrados para este item.</p>`;
            }}
            modal.style.display = 'flex';
        }});
    }});
}});
</script>

</body>
</html>
"""

# === Salva HTML ===
with output_html_path.open("w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ HTML gerado com sucesso: {output_html_path}")
