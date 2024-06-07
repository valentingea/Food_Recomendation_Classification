FROM python:3.11-slim

RUN apt-get update && apt-get install build-essential -y
RUN apt-get install -y curl wget git

WORKDIR /app

COPY . .
