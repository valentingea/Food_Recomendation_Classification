FROM python:3.11-slim

RUN apt-get update && apt-get install build-essential -y
RUN apt-get install -y curl wget git

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
