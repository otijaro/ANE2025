FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY web_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

COPY web_api/ /app/web_api/
COPY h_simulador/ /app/h_simulador/

EXPOSE 8000
CMD ["uvicorn", "web_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
