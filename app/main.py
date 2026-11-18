from fastapi.responses import HTMLResponse
import uuid
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Inicialização com metadados claros
app = FastAPI(title="Phishing Detection API", version="1.3")

# Carregamento seguro do modelo
try:
    model = joblib.load('random_forest_phishing.pkl')
except FileNotFoundError:
    model = None
    print("Aviso: Modelo 'random_forest_phishing.pkl' não encontrado.")

# Esquema de dados com validação de limites (Segurança)
class EmailInput(BaseModel):
    has_link: int = Field(..., ge=0, le=1, description="0 (Não) ou 1 (Sim)")
    has_attachment: int = Field(..., ge=0, le=1, description="0 (Não) ou 1 (Sim)")
    urgency_score: int = Field(..., ge=0, le=10, description="Escala de urgência de 0 a 10")
    spelling_errors: int = Field(..., ge=0, description="Número total de erros ortográficos")
    email_length_words: int = Field(..., gt=0, description="Número de palavras (> 0)")

@app.get("/", response_class=HTMLResponse, summary="Interface Gráfica")
def interface_grafica():
    html_content = r"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema Anti-Phishing</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
            .container { background-color: white; padding: 28px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 500px; }
            h2 { color: #1a73e8; text-align: center; margin-top: 0; margin-bottom: 18px; }
            .extractor-box { background-color: #f8f9fa; border: 1px solid #dfe1e5; border-radius: 8px; padding: 14px; margin-bottom: 18px; }
            .extractor-box label { color: #1a73e8; font-size: 14px; }
            textarea { width: 100%; height: 85px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-family: inherit; font-size: 13px; resize: vertical; margin-bottom: 8px; }
            .btn-extract { width: 100%; padding: 8px; background-color: #34a853; color: white; border: none; border-radius: 5px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; }
            .btn-extract:hover { background-color: #2c8e46; }
            #link-alerta { font-size: 12px; margin-top: 8px; color: #b06000; font-weight: 600; display: none; }
            .grid-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px; }
            .form-group { margin-bottom: 0; }
            .form-group.full { grid-column: span 2; }
            label { display: block; font-weight: bold; margin-bottom: 5px; color: #333; font-size: 13px; }
            input { width: 100%; padding: 9px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
            .btn-predict { width: 100%; padding: 12px; background-color: #1a73e8; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
            .btn-predict:hover { background-color: #1557b0; }

            /* Estilos do Mini-Relatório */
            #relatorio { margin-top: 22px; border-radius: 8px; overflow: hidden; border: 1px solid #dcdcdc; display: none; font-size: 13.5px; }
            .relatorio-header { padding: 14px 16px; font-weight: bold; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }
            .relatorio-header.legitimo { background-color: #d4edda; color: #155724; border-bottom: 1px solid #c3e6cb; }
            .relatorio-header.phishing { background-color: #f8d7da; color: #721c24; border-bottom: 1px solid #f5c6cb; }
            .badge { padding: 3px 8px; border-radius: 12px; font-size: 11px; text-transform: uppercase; background: rgba(255,255,255,0.7); }
            .relatorio-body { padding: 16px; background-color: #fafafa; color: #333; }
            .relatorio-sec { margin-bottom: 12px; }
            .relatorio-sec:last-child { margin-bottom: 0; }
            .relatorio-titulo { font-weight: bold; color: #1a73e8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }
            .relatorio-lista { margin: 0; padding-left: 18px; line-height: 1.55; }
            .recomendacao-box { background-color: #fff; border-left: 3px solid #1a73e8; padding: 8px 10px; border-radius: 4px; font-size: 13px; }
            .relatorio-footer { display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; background-color: #f1f3f4; border-top: 1px solid #e0e0e0; font-size: 11px; color: #666; }
            .btn-copy { background-color: #fff; border: 1px solid #ccc; border-radius: 4px; padding: 4px 10px; font-size: 11.5px; font-weight: 600; cursor: pointer; color: #333; }
            .btn-copy:hover { background-color: #e8eaed; }
        </style>
    </head>
    <body>

    <div class="container">
        <h2>Detetor de Phishing</h2>

        <div class="extractor-box">
            <label for="texto_email">Colar Texto do E-mail (Preenchimento Automático)</label>
            <textarea id="texto_email" placeholder="Cole aqui o conteúdo do e-mail para extrair os indicadores automaticamente..."></textarea>
            <button type="button" class="btn-extract" onclick="extrairMetricas()">⚡ Extrair Indicadores do Texto</button>
            <div id="link-alerta"></div>
        </div>
        
        <div class="grid-inputs">
            <div class="form-group">
                <label>Tem Link? (0 ou 1)</label>
                <input type="number" id="has_link" min="0" max="1" value="1">
            </div>
            <div class="form-group">
                <label>Tem Anexo? (0 ou 1)</label>
                <input type="number" id="has_attachment" min="0" max="1" value="0">
            </div>
            <div class="form-group">
                <label>Urgência (0 a 10)</label>
                <input type="number" id="urgency_score" min="0" max="10" value="5">
            </div>
            <div class="form-group">
                <label>Erros / Anomalias</label>
                <input type="number" id="spelling_errors" min="0" value="2">
            </div>
            <div class="form-group full">
                <label>Tamanho (Nº de Palavras)</label>
                <input type="number" id="email_length_words" min="1" value="150">
            </div>
        </div>
        
        <button class="btn-predict" onclick="fazerPredicao()">Analisar E-mail</button>

        <div id="relatorio"></div>
    </div>

    <script>
        let detalheLinkSuspeito = "";
        let textoRelatorioAtual = "";

        function extrairMetricas() {
            const texto = document.getElementById('texto_email').value.trim();
            if (!texto) {
                alert("Cole primeiro o texto de um e-mail na caixa acima.");
                return;
            }

            // 1. Contagem de palavras
            const palavras = texto.split(/\s+/).filter(p => p.length > 0);
            document.getElementById('email_length_words').value = Math.max(1, palavras.length);

            // 2. Deteção de Links e análise básica de risco na URL
            const regexLink = /(https?:\/\/[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|pt|net|org|xyz|top|info|tk|ml))/gi;
            const linksEncontrados = texto.match(regexLink);
            const temLink = linksEncontrados ? 1 : 0;
            document.getElementById('has_link').value = temLink;

            const divAlertaLink = document.getElementById('link-alerta');
            detalheLinkSuspeito = "";

            if (temLink) {
                const urlSuspeita = linksEncontrados.some(u =>
                    u.toLowerCase().startsWith('http://') ||
                    /\d+\.\d+\.\d+\.\d+/.test(u) ||
                    /(bit\.ly|tinyurl|\.xyz|\.top|\.tk)/i.test(u)
                );
                divAlertaLink.style.display = 'block';
                if (urlSuspeita) {
                    detalheLinkSuspeito = "URL suspeita detetada (HTTP sem encriptação, IP direto ou domínio encurtado)";
                    divAlertaLink.textContent = "⚠️ " + detalheLinkSuspeito + ".";
                } else {
                    divAlertaLink.textContent = "🔗 Link detetado no corpo da mensagem.";
                }
            } else {
                divAlertaLink.style.display = 'none';
            }

            // 3. Deteção de menção a anexos
            const temAnexo = /(\.pdf|\.exe|\.zip|\.rar|\.docx?|\.xlsx?|em anexo|segue anexo|ficheiro anexo|attached)/i.test(texto) ? 1 : 0;
            document.getElementById('has_attachment').value = temAnexo;

            // 4. Cálculo do Nível de Urgência (0 a 10)
            const palavrasUrgencia = [
                'urgente', 'imediato', 'imediatamente', 'bloqueada', 'bloqueio',
                'suspensa', 'suspensão', '24 horas', '48 horas', 'último aviso',
                'verifique', 'confirmar conta', 'senha', 'password', 'clique aqui',
                'prémio', 'ganhou', 'fatura em atraso', 'urgent', 'immediately', 'suspended'
            ];
            const textoMinusculo = texto.toLowerCase();
            let scoreUrgencia = 0;

            palavrasUrgencia.forEach(termo => {
                if (textoMinusculo.includes(termo)) scoreUrgencia += 2;
            });

            const exclamacoes = (texto.match(/!/g) || []).length;
            scoreUrgencia += Math.min(3, exclamacoes);
            document.getElementById('urgency_score').value = Math.min(10, scoreUrgencia);

            // 5. Deteção de anomalias de escrita / ofuscação típica de phishing
            let anomalias = 0;
            anomalias += (texto.match(/\b[a-zA-Z]+[0-9@$][a-zA-Z]+\b/g) || []).length;
            anomalias += (texto.match(/[!?]{2,}/g) || []).length;
            anomalias += (texto.match(/[a-zA-Z][.,][a-zA-Z]{2,}/g) || []).length;
            document.getElementById('spelling_errors').value = anomalias;
        }

        async function fazerPredicao() {
            const dados = {
                has_link: parseInt(document.getElementById('has_link').value) || 0,
                has_attachment: parseInt(document.getElementById('has_attachment').value) || 0,
                urgency_score: parseInt(document.getElementById('urgency_score').value) || 0,
                spelling_errors: parseInt(document.getElementById('spelling_errors').value) || 0,
                email_length_words: parseInt(document.getElementById('email_length_words').value) || 1
            };

            const resposta = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            const divRelatorio = document.getElementById('relatorio');
            divRelatorio.style.display = 'block';

            if (!resposta.ok) {
                divRelatorio.innerHTML = `<div class="relatorio-header phishing">⚠️ Erro de Validação: Verifique se os valores estão dentro dos limites permitidos.</div>`;
                return;
            }

            const resultado = await resposta.json();
            const probPercent = (resultado.phishing_probability * 100).toFixed(1);
            const dataHora = new Date().toLocaleString('pt-PT');

            // Classificação de nível de risco
            let nivelRisco = "Baixo";
            if (resultado.phishing_probability >= 0.7) nivelRisco = "Elevado";
            else if (resultado.phishing_probability >= 0.45) nivelRisco = "Moderado";

            // Construção dos pontos de diagnóstico
            const fatores = [];
            if (dados.has_link === 1) {
                fatores.push(detalheLinkSuspeito ? `Ligação externa com alerta: ${detalheLinkSuspeito}.` : "Presença de ligação externa (link) no e-mail.");
            } else {
                fatores.push("Sem ligações externas detetadas.");
            }

            if (dados.has_attachment === 1) {
                fatores.push("Contém ou referencia ficheiro em anexo (vetor comum de malware).");
            }

            if (dados.urgency_score >= 6) {
                fatores.push(`Pressão psicológica elevada (Urgência: ${dados.urgency_score}/10).`);
            } else {
                fatores.push(`Nível de urgência controlado (${dados.urgency_score}/10).`);
            }

            if (dados.spelling_errors > 0) {
                fatores.push(`Foram identificadas ${dados.spelling_errors} anomalia(s) de escrita ou ofuscação.`);
            }

            fatores.push(`Extensão analisada: ${dados.email_length_words} palavra(s).`);

            const recomendacao = resultado.is_phishing
                ? "Não clique em links nem abra anexos. Confirme a autenticidade do remetente através de um canal oficial antes de tomar qualquer ação."
                : "Os indicadores estruturais analisados não apontam para fraude. Ainda assim, confirme sempre o domínio do remetente caso sejam pedidos dados sensíveis.";

            const classeHeader = resultado.is_phishing ? 'phishing' : 'legitimo';
            const tituloVeredito = resultado.is_phishing
                ? `⚠️ PHISHING DETETADO (${probPercent}%)`
                : `✅ E-MAIL LEGÍTIMO (${probPercent}% risco)`;

            // Guardar versão em texto simples para o botão Copiar
            textoRelatorioAtual = [
                `=== MINI-RELATÓRIO DE ANÁLISE ANTI-PHISHING ===`,
                `Data/Hora: ${dataHora}`,
                `ID Análise: ${resultado.prediction_id}`,
                `Veredito: ${resultado.is_phishing ? 'PHISHING' : 'LEGÍTIMO'} (Probabilidade: ${probPercent}% | Risco: ${nivelRisco})`,
                ``,
                `Indicadores Avaliados:`,
                ...fatores.map(f => `- ${f}`),
                ``,
                `Recomendação: ${recomendacao}`
            ].join('\n');

            divRelatorio.innerHTML = `
                <div class="relatorio-header ${classeHeader}">
                    <span>${tituloVeredito}</span>
                    <span class="badge">Risco ${nivelRisco}</span>
                </div>
                <div class="relatorio-body">
                    <div class="relatorio-sec">
                        <div class="relatorio-titulo">Resumo dos Indicadores Analisados</div>
                        <ul class="relatorio-lista">
                            ${fatores.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="relatorio-sec">
                        <div class="relatorio-titulo">Recomendação de Segurança</div>
                        <div class="recomendacao-box">${recomendacao}</div>
                    </div>
                </div>
                <div class="relatorio-footer">
                    <span>ID: ${resultado.prediction_id.slice(0, 8)}... | ${dataHora}</span>
                    <button type="button" class="btn-copy" onclick="copiarRelatorio(this)">📋 Copiar Relatório</button>
                </div>
            `;
        }

        function copiarRelatorio(botao) {
            navigator.clipboard.writeText(textoRelatorioAtual).then(() => {
                const textoOriginal = botao.textContent;
                botao.textContent = "✅ Copiado!";
                setTimeout(() => { botao.textContent = textoOriginal; }, 2000);
            });
        }
    </script>

    </body>
    </html>
    """
    return html_content

@app.post("/predict")
def predict(data: EmailInput):
    """
    Recebe as 5 métricas de um e-mail validadas pelo Pydantic,
    transforma-as num DataFrame e utiliza o modelo Random Forest 
    para prever a probabilidade de ser phishing.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo não disponível no servidor.")
    
    input_data = pd.DataFrame([data.model_dump()])
    
    prediction = int(model.predict(input_data)[0])
    prediction_prob = round(float(model.predict_proba(input_data)[0][1]), 4)
    
    return {
        "prediction_id": str(uuid.uuid4()),
        "is_phishing": bool(prediction),
        "phishing_probability": prediction_prob
    }