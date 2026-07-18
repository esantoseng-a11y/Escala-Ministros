import os
import calendar
import webbrowser
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, send_file

# Importações do ReportLab para gerar o PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    print("Por favor, instale 'reportlab' no Pip do Pydroid 3.")

app = Flask(__name__)

# Caminhos de arquivos no Android (Pydroid 3)
PASTA_HOME = os.path.expanduser("~")
ARQUIVO_MINISTROS = os.path.join(PASTA_HOME, "ministros.txt")

# Função para carregar ministros salvos em ordem alfabética ou criar lista padrão
def carregar_ministros():
    if os.path.exists(ARQUIVO_MINISTROS):
        try:
            with open(ARQUIVO_MINISTROS, "r", encoding="utf-8") as f:
                nomes = [linha.strip() for linha in f.readlines() if linha.strip()]
                nomes.sort(key=str.lower)
                nomes = nomes[:80]
                while len(nomes) < 80:
                    nomes.append(f"Ministro {len(nomes) + 1}")
                return nomes
        except Exception as e:
            print("Erro ao carregar ministros:", e)
            
    lista_padrao = [f"Ministro {i:02d}" for i in range(1, 81)]
    return lista_padrao

# Salvar lista no arquivo txt
def salvar_ministros_no_disco(lista_nomes):
    try:
        with open(ARQUIVO_MINISTROS, "w", encoding="utf-8") as f:
            for nome in lista_nomes:
                f.write(nome + "\n")
    except Exception as e:
        print(f"Erro ao salvar arquivo de ministros: {e}")

# Dados salvos em memória
dados_sistema = {
    "ano": 2026,
    "mes": 1,
    "igrejas_selecionadas": ["Matriz"],
    "ministros": carregar_ministros(),
    "escala_dados": [],
    "observacoes": "Nota: Os ministros impossibilitados de comparecer deverão providenciar substituto com antecedência.",
    "avisos": [],
    "verificado": False
}

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Escala de Ministros — Nsa. Sra. do Divino Livramento</title>
    <style>
        :root {
            --primary: #1a365d;
            --secondary: #d69e2e;
            --bg: #f7fafc;
            --card-bg: #ffffff;
            --text: #2d3748;
            --danger: #e53e3e;
            --success: #38a169;
            --warning: #dd6b20;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 15px;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        .content {
            flex: 1;
        }
        .header {
            text-align: center;
            background-color: var(--primary);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .header h1 { margin: 0; font-size: 1.5rem; }
        .header p { margin: 5px 0 0 0; font-size: 0.9rem; color: #cbd5e0; }
        .card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .alert {
            background-color: #fff5f5;
            border-left: 4px solid var(--danger);
            color: var(--danger);
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }
        .success-alert {
            background-color: #f0fff4;
            border-left: 4px solid var(--success);
            color: var(--success);
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9rem;
        }
        input, select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #cbd5e0;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 1rem;
            background-color: white;
            font-family: inherit;
        }
        textarea {
            resize: vertical;
            height: 80px;
        }
        .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 5px;
        }
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.95rem;
        }
        .checkbox-item input {
            width: auto;
        }
        button {
            width: 100%;
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background-color: #2b6cb0; }
        .btn-add { background-color: var(--secondary); }
        .btn-add:hover { background-color: #b7791f; }
        .btn-verify { background-color: var(--warning); margin-bottom: 15px; }
        .btn-verify:hover { background-color: #dd6b20; }
        .btn-pdf { background-color: var(--success); }
        .btn-pdf:hover { background-color: #2f855a; }
        .dia-item {
            border-left: 4px solid var(--primary);
            background: #edf2f7;
            padding: 12px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 15px;
        }
        .dia-item h4 { margin: 0 0 5px 0; color: var(--primary); }
        .dia-item p { margin: 2px 0; font-size: 0.85rem; }
        .ministros-select {
            height: 120px;
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .footer {
            text-align: center;
            padding: 20px 10px;
            margin-top: 30px;
            border-top: 1px solid #e2e8f0;
            font-size: 0.85rem;
            color: #718096;
            background-color: #edf2f7;
            border-radius: 8px;
        }
        .footer strong {
            color: var(--primary);
        }
    </style>
</head>
<body>

    <div class="content">
        <div class="header">
            <h1>† ESCALA DE MINISTROS †</h1>
            <p>Paróquia Nossa Senhora do Divino Livramento — Gestão Pastoral</p>
        </div>

        <!-- Seção de Alertas e Inconsistências Globais -->
        {% if dados.verificado %}
            {% if dados.avisos %}
            <div class="alert">
                <h4 style="margin: 0 0 10px 0;">⚠️ Conflitos de Ministros no Mesmo Fim de Semana / Semana:</h4>
                <p style="font-size: 0.8rem; margin: 0 0 10px 0; color: #742a2a;">Aviso: O mesmo ministro não pode atuar em celebrações diferentes no mesmo período semanal (incluindo extras).</p>
                <ul style="margin: 0; padding-left: 20px; line-height: 1.5;">
                    {% for aviso in dados.avisos %}
                    <li>{{ aviso | safe }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% else %}
            <div class="success-alert">
                <h4 style="margin: 0;">✅ Escala 100% Consistente! Nenhum ministro está repetido no mesmo período semanal.</h4>
            </div>
            {% endif %}
        {% endif %}

        <!-- 1. Configurar Período Base e Igrejas Ativas -->
        <div class="card">
            <h3>1. Configurar Mês de Referência</h3>
            <p style="font-size: 0.8rem; color: #718096; margin-top: -10px; margin-bottom: 15px;">Nota: Quartas-feiras e Sábados serão gerados apenas para a <b>Matriz</b>. Domingos serão gerados para todas as igrejas selecionadas.</p>
            <form action="/gerar_datas" method="POST">
                <div class="grid-2">
                    <div class="form-group">
                        <label>Ano:</label>
                        <input type="number" name="ano" value="{{ dados.ano }}">
                    </div>
                    <div class="form-group">
                        <label>Mês (1-12):</label>
                        <input type="number" name="mes" value="{{ dados.mes }}" min="1" max="12">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Selecione as Igrejas Ativas para os Domingos:</label>
                    <div class="checkbox-group">
                        <div class="checkbox-item">
                            <input type="checkbox" name="igrejas" value="Matriz" {% if "Matriz" in dados.igrejas_selecionadas %}checked{% endif %}> Matriz
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="igrejas" value="Santos Reis" {% if "Santos Reis" in dados.igrejas_selecionadas %}checked{% endif %}> Santos Reis
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" name="igrejas" value="Capela Nossa Senhora Aparecida" {% if "Capela Nossa Senhora Aparecida" in dados.igrejas_selecionadas %}checked{% endif %}> Capela Nossa Senhora Aparecida
                        </div>
                    </div>
                </div>
                
                <button type="submit">Gerar Escala de Datas</button>
            </form>
        </div>

        <!-- 2. Adicionar Missa/Novena Extra -->
        <div class="card" style="border: 1px solid #e2e8f0;">
            <h3>➕ Adicionar Missa / Novena / Celebração Extra</h3>
            <form action="/adicionar_extra" method="POST">
                <div class="grid-2">
                    <div class="form-group">
                        <label>Data (DD/MM/AAAA):</label>
                        <input type="text" name="data_extra" placeholder="Ex: 12/05/2026" required>
                    </div>
                    <div class="form-group">
                        <label>Horário:</label>
                        <input type="text" name="horario_extra" placeholder="Ex: 19:30" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Local / Capela / Igreja (Digitação Livre):</label>
                    <input type="text" name="igreja_extra" placeholder="Ex: Capela Rural Santo Expedito" required>
                </div>
                <div class="form-group">
                    <label>Dia da Semana:</label>
                    <select name="dia_semana_extra">
                        <option value="Segunda-feira">Segunda-feira</option>
                        <option value="Terça-feira">Terça-feira</option>
                        <option value="Quarta-feira">Quarta-feira</option>
                        <option value="Quinta-feira">Quinta-feira</option>
                        <option value="Sexta-feira">Sexta-feira</option>
                        <option value="Sábado">Sábado</option>
                        <option value="Domingo">Domingo</option>
                    </select>
                </div>
                <button type="submit" class="btn-add">Incluir Celebração Extra</button>
            </form>
        </div>

        <!-- 3. Lista de Celebrações -->
        {% if dados.escala_dados %}
        <div class="card">
            <h3>2. Escalar Ministros por Celebração</h3>
            
            <a href="/verificar_inconsistencias" style="text-decoration: none;"><button class="btn-verify" type="button">🔍 Verificar Inconsistências (Duplicidades)</button></a>
            
            {% for dia in dados.escala_dados %}
            <div class="dia-item">
                <h4>{{ dia.data }} ({{ dia.dia_semana }})</h4>
                <p><strong>Local:</strong> {{ dia.igreja }} às {{ dia.horario }}</p>
                <p><strong>Ministros Escalados:</strong> 
                    {% if dia.ministros %}
                        <span style="color: var(--success); font-weight: bold;">{{ dia.ministros | join(', ') }}</span>
                    {% else: %}
                        <span style="color: var(--danger); font-weight: bold;">Nenhum ministro escalado</span>
                    {% endif %}
                </p>
                
                <form action="/salvar_dia/{{ loop.index0 }}" method="POST" style="margin-top: 10px;">
                    <label style="font-size: 0.8rem;">Selecione os Ministros (em ordem alfabética):</label>
                    <select name="ministros_selecionados" class="ministros-select" multiple>
                        {% for ministro in dados.ministros %}
                        <option value="{{ ministro }}" {% if ministro in dia.ministros %}selected{% endif %}>{{ ministro }}</option>
                        {% endfor %}
                    </select>
                    <button type="submit" style="padding: 6px; font-size: 0.85rem; margin-top: 5px; background-color: var(--primary);">Atualizar Escala deste Dia</button>
                </form>
            </div>
            {% endfor %}
        </div>

        <!-- 4. Observações da Escala -->
        <div class="card">
            <h3>📝 Observações para o PDF</h3>
            <p style="font-size: 0.8rem; color: #718096; margin-top: -10px; margin-bottom: 10px;">Este texto aparecerá dentro de um quadro explicativo na parte inferior da folha impressa.</p>
            <form action="/salvar_observacoes" method="POST">
                <div class="form-group">
                    <textarea name="observacoes">{{ dados.observacoes }}</textarea>
                </div>
                <button type="submit" style="background-color: var(--primary); padding: 8px; font-size: 0.9rem;">Atualizar Texto de Observação</button>
            </form>
        </div>

        <!-- 5. Gerar PDF -->
        <div class="card" style="background-color: #f0fff4; border: 1px solid #c6f6d5; text-align: center;">
            <h3>3. Concluir e Imprimir</h3>
            <p>Gere o arquivo PDF final organizado com todas as igrejas, celebrações extras e o quadro de observações.</p>
            <a href="/gerar_pdf" style="text-decoration: none;"><button class="btn-pdf" type="button">📥 Baixar PDF da Escala</button></a>
        </div>
        {% endif %}

        <!-- 6. Cadastro de Ministros -->
        <div class="card">
            <h3>📋 Cadastro de Ministros (Salva e Ordena Automaticamente)</h3>
            <p style="font-size: 0.8rem; color: #718096; margin-top: -10px; margin-bottom: 15px;">Ao clicar em Salvar, todos os nomes serão gravados e reordenados alfabeticamente.</p>
            <form action="/salvar_ministros" method="POST">
                <div style="max-height: 250px; overflow-y: auto; border: 1px solid #cbd5e0; padding: 10px; border-radius: 6px; background-color: #faf5ff;">
                    {% for i in range(80) %}
                    <div class="form-group" style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 0.85rem; width: 40px; font-weight: bold; color: var(--primary);">#{{ i+1 }}</span>
                        <input type="text" name="min_{{ i }}" value="{{ dados.ministros[i] }}" style="padding: 5px;">
                    </div>
                    {% endfor %}
                </div>
                <button type="submit" style="margin-top: 10px; background-color: #4a5568;">💾 Salvar e Ordenar Alfabeticamente</button>
            </form>
        </div>
    </div>

    <!-- Rodapé solicitado -->
    <div class="footer">
        Desenvolvido para a <strong>Paróquia Nossa Senhora do Divino Livramento</strong><br>
        Created by <strong>Eng. Evandro Santos</strong>
    </div>

</body>
</html>
"""

def analisar_duplicidades():
    """
    Verifica se o mesmo ministro está escalado em mais de uma celebração
    na mesma semana litúrgica (considerando Segunda a Domingo do calendário).
    """
    dados_sistema["avisos"] = []
    lista_escalas = dados_sistema["escala_dados"]
    
    por_semana = {}
    
    for item in lista_escalas:
        try:
            data_obj = datetime.strptime(item["data"], "%d/%m/%Y").date()
            ano_iso, num_semana, _ = data_obj.isocalendar()
            chave_semana = f"{ano_iso}-W{num_semana:02d}"
            
            if chave_semana not in por_semana:
                por_semana[chave_semana] = []
            por_semana[chave_semana].append(item)
        except Exception as e:
            print(f"Erro ao processar data {item['data']}: {e}")

    for chave, celebracoes in por_semana.items():
        for i, cel_a in enumerate(celebracoes):
            for j, cel_b in enumerate(celebracoes):
                if i >= j:
                    continue
                
                comuns = set(cel_a["ministros"]).intersection(set(cel_b["ministros"]))
                
                for ministro in comuns:
                    if ministro.strip():
                        msg = (
                            f"O ministro <b>{ministro}</b> está escalado duas vezes na mesma semana:<br/>"
                            f"• {cel_a['data']} ({cel_a['dia_semana']}) na <b>{cel_a['igreja']}</b><br/>"
                            f"• {cel_b['data']} ({cel_b['dia_semana']}) na <b>{cel_b['igreja']}</b>"
                        )
                        if msg not in dados_sistema["avisos"]:
                            dados_sistema["avisos"].append(msg)

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE, dados=dados_sistema)

@app.route('/verificar_inconsistencias')
def verificar_inconsistencias():
    analisar_duplicidades()
    dados_sistema["verificado"] = True
    return redirect(url_for('index'))

@app.route('/gerar_datas', methods=['POST'])
def gerar_datas():
    dados_sistema["ano"] = int(request.form.get("ano"))
    dados_sistema["mes"] = int(request.form.get("mes"))
    dados_sistema["igrejas_selecionadas"] = request.form.getlist("igrejas")
    dados_sistema["verificado"] = False
    dados_sistema["escala_dados"] = []
    
    if not dados_sistema["igrejas_selecionadas"]:
        dados_sistema["igrejas_selecionadas"] = ["Matriz"]
        
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)
    
    for dia, dia_semana in c.itermonthdays2(dados_sistema["ano"], dados_sistema["mes"]):
        if dia != 0 and dia_semana in [2, 5, 6]:  
            dia_str = f"{dia:02d}/{dados_sistema['mes']:02d}/{dados_sistema['ano']}"
            
            # Quarta-feira (Apenas Matriz)
            if dia_semana == 2:
                dados_sistema["escala_dados"].append({
                    "data": dia_str,
                    "dia_semana": "Quarta-feira",
                    "igreja": "Matriz",
                    "horario": "19:00",
                    "ministros": []
                })
                
            # Sábado (Apenas Matriz)
            elif dia_semana == 5:
                dados_sistema["escala_dados"].append({
                    "data": dia_str,
                    "dia_semana": "Sábado",
                    "igreja": "Matriz",
                    "horario": "19:30",
                    "ministros": []
                })
                
            # Domingo (Todas as igrejas selecionadas)
            elif dia_semana == 6:
                for igreja in dados_sistema["igrejas_selecionadas"]:
                    dados_sistema["escala_dados"].append({
                        "data": dia_str,
                        "dia_semana": "Domingo",
                        "igreja": igreja,
                        "horario": "07:00" if "Matriz" in igreja else "08:30",
                        "ministros": []
                    })
            
    dados_sistema["escala_dados"].sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
    return redirect(url_for('index'))

@app.route('/adicionar_extra', methods=['POST'])
def adicionar_extra():
    data_ext = request.form.get("data_extra").strip()
    hora_ext = request.form.get("horario_extra").strip()
    igreja_ext = request.form.get("igreja_extra").strip()
    dia_sem_ext = request.form.get("dia_semana_extra")
    dados_sistema["verificado"] = False
    
    if data_ext and hora_ext and igreja_ext:
        dados_sistema["escala_dados"].append({
            "data": data_ext,
            "dia_semana": dia_sem_ext,
            "igreja": igreja_ext,
            "horario": hora_ext,
            "ministros": []
        })
        try:
            dados_sistema["escala_dados"].sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"))
        except Exception:
            pass
            
    return redirect(url_for('index'))

@app.route('/salvar_dia/<int:dia_id>', methods=['POST'])
def salvar_dia(dia_id):
    ministros_selecionados = request.form.getlist("ministros_selecionados")
    dados_sistema["escala_dados"][dia_id]["ministros"] = ministros_selecionados
    dados_sistema["verificado"] = False
    return redirect(url_for('index'))

@app.route('/salvar_observacoes', methods=['POST'])
def salvar_observacoes():
    dados_sistema["observacoes"] = request.form.get("observacoes").strip()
    return redirect(url_for('index'))

@app.route('/salvar_ministros', methods=['POST'])
def salvar_ministros():
    novos_nomes = []
    for i in range(80):
        nome_editado = request.form.get(f"min_{i}").strip()
        if nome_editado:
            novos_nomes.append(nome_editado)
        else:
            novos_nomes.append(f"Ministro {i+1}")
            
    novos_nomes.sort(key=str.lower)
    dados_sistema["ministros"] = novos_nomes
    salvar_ministros_no_disco(novos_nomes)
    return redirect(url_for('index'))

@app.route('/gerar_pdf')
def gerar_pdf():
    filepath = os.path.join(PASTA_HOME, "escala_ministros.pdf")
    
    doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    titulo_style = ParagraphStyle(
        'TituloLiturgico', parent=styles['Heading1'],
        fontSize=14, leading=16, alignment=1,
        textColor=colors.HexColor('#1a365d'), spaceAfter=5
    )
    
    sub_style = ParagraphStyle(
        'SubLiturgico', parent=styles['Normal'],
        fontSize=10, leading=12, alignment=1,
        textColor=colors.HexColor('#4a5568'), spaceAfter=15
    )
    
    story.append(Paragraph("† ESCALA DE MINISTROS DA SAGRADA COMUNHÃO †", titulo_style))
    story.append(Paragraph(f"Referência Pastoral: {dados_sistema['mes']:02d}/{dados_sistema['ano']} — Paróquia Nsa. Sra. do Divino Livramento", sub_style))
    
    tabela_dados = [["DATA / DIA", "PARÓQUIA / LOCAL", "HORÁRIO", "MINISTROS ESCALADOS"]]
    cell_body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=8, leading=10)
    
    for item in dados_sistema["escala_dados"]:
        ministros_str = ", ".join(item["ministros"]) if item["ministros"] else "Nenhum ministro escalado"
        tabela_dados.append([
            Paragraph(f"<b>{item['data']}</b><br/>({item['dia_semana']})", cell_body_style),
            Paragraph(item['igreja'], cell_body_style),
            Paragraph(item['horario'], cell_body_style),
            Paragraph(ministros_str, cell_body_style)
        ])
        
    tabela = Table(tabela_dados, colWidths=[90, 130, 70, 250])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(tabela)
    story.append(Spacer(1, 15))
    
    obs_titulo_style = ParagraphStyle('ObsTitulo', parent=styles['Normal'], fontSize=9, leading=11, fontName="Helvetica-Bold", textColor=colors.HexColor('#1a365d'))
    obs_texto_style = ParagraphStyle('ObsTexto', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#2d3748'))
    
    obs_html = dados_sistema["observacoes"].replace("\n", "<br/>")
    
    dados_quadro = [
        [Paragraph("<b>OBSERVAÇÕES IMPORTANTES</b>", obs_titulo_style)],
        [Paragraph(obs_html, obs_texto_style)]
    ]
    
    quadro_obs = Table(dados_quadro, colWidths=[540])
    quadro_obs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d69e2e')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(quadro_obs)
    doc.build(story)
    
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
