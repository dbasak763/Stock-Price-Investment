FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY config.yml ./

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

ENTRYPOINT ["python", "src/main.py"]
