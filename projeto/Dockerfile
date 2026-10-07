FROM python:3.12-slim
WORKDIR /app
COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY src/ src/
COPY models/ models/
COPY static/ static/
COPY api.py .
EXPOSE 8000
CMD ["python","-m","uvicorn","api:app","--host","0.0.0.0","--port","8000"]
