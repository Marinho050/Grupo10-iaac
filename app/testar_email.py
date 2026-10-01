import joblib
import pandas as pd

# 1. Carregar o modelo treinado
modelo = joblib.load('random_forest_phishing.pkl')

# 2. Inserir as caraterísticas de um e-mail para teste
dados_email = {
    'has_link': [1],           # Tem link malicioso
    'has_attachment': [1],     # Tem anexo
    'urgency_score': [5],      # Urgência máxima
    'spelling_errors': [10],   # Muitos erros ortográficos (caraterística típica de phishing mal feito)
    'email_length_words': [5]  # E-mail extremamente curto (apenas a exigir ações rápidas)
}

df_novo_email = pd.DataFrame(dados_email)

# 3. Gerar a previsão e obter probabilidades
previsao = modelo.predict(df_novo_email)
probabilidades = modelo.predict_proba(df_novo_email)

# 4. Apresentar o veredicto e a confiança do modelo
print("=== Análise de Segurança ===")
if previsao[0] == 1:
    print(f"🚨 ALERTA: E-mail classificado como PHISHING.")
else:
    print(f"✅ SEGURO: E-mail classificado como Legítimo.")

print(f"Confiança do modelo -> Legítimo: {probabilidades[0][0]*100:.2f}% | Phishing: {probabilidades[0][1]*100:.2f}%")

# 5. Ver a importância de cada caraterística no modelo global
print("\n=== Importância das Caraterísticas no Modelo ===")
importancias = modelo.feature_importances_
colunas = ['has_link', 'has_attachment', 'urgency_score', 'spelling_errors', 'email_length_words']

for coluna, importancia in zip(colunas, importancias):
    print(f"- {coluna}: {importancia * 100:.2f}%")