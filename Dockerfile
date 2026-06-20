FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    default-jdk \
    maven \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY java/ java/
RUN cd java && mvn -B clean package -DskipTests

COPY web/ web/
WORKDIR /app/web
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
