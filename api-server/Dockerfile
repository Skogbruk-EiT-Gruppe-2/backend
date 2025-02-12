FROM python:3.10-slim
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY ./app ./app
EXPOSE 443
CMD ["fastapi", "run", "app/main.py", "--port", "443"]