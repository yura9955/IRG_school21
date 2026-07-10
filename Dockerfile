FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /src
USER appuser

CMD ["python", "-m", "src.main"]
