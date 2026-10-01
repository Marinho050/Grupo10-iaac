import requests

url = "http://127.0.0.1:8000/predict"
dados_email = {
    "has_link": 1,
    "has_attachment": 1,
    "urgency_score": 5,
    "spelling_errors": 4,
    "email_length_words": 15
}

resposta = requests.post(url, json=dados_email)
print("Resposta da API:", resposta.json())