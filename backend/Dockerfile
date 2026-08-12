FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/app

WORKDIR /app

COPY requirements.txt .
RUN pip install \
    --no-cache-dir \
    --timeout 120 \
    --retries 5 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.6.0+cpu

RUN pip install \
    --no-cache-dir \
    --timeout 120 \
    --retries 5 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
