FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD gunicorn -w 2 -t 120 -b 0.0.0.0:$PORT app:app
