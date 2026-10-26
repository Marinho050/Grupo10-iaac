import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# 1. Carregar os Dados
# O ficheiro CSV deve estar na mesma pasta que este script
df = pd.read_csv('phishing_emails.csv')

# Limpeza: Remover linhas com dados em falta
df = df.dropna()

# 2. Seleção de Features
# Filtrar apenas as colunas com valores numéricos para o algoritmo analisar
colunas_preditivas = ['has_link', 'has_attachment', 'urgency_score', 'spelling_errors', 'email_length_words']

X = df[colunas_preditivas] # Variáveis independentes (pistas)
y = df['is_phishing']      # Variável dependente (resultado alvo)

# 3. Divisão dos Dados (Train-Test Split)
# Separar 80% dos dados para treino e guardar 20% para teste cego
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Treino do Modelo
# Instanciar o algoritmo Random Forest (excelente para classificação estruturada)
modelo = RandomForestClassifier(random_state=42)

# Alimentar o modelo com os 80% de dados de treino
modelo.fit(X_train, y_train)

# 5. Previsão e Avaliação
# Forçar o modelo a tentar adivinhar se os e-mails dos 20% restantes são phishing
previsoes = modelo.predict(X_test)

# Imprimir as métricas no ecrã
print("=== Relatório de Classificação ===")
print(classification_report(y_test, previsoes))

print("\n=== Matriz de Confusão ===")
print(confusion_matrix(y_test, previsoes))

import joblib

# Guarda o modelo treinado num ficheiro para uso futuro
joblib.dump(modelo, 'random_forest_phishing.pkl')
print("\nModelo guardado com sucesso!")