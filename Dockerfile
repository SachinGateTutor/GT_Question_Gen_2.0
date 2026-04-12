# Python 3.13 (aligned with EC2 / local dev)
FROM python:3.13-slim

WORKDIR /app

# graphviz: `dot` for diagram generation; curl: HEALTHCHECK
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p app/static/images logs

ENV FLASK_APP=app/main.py
ENV FLASK_ENV=production
ENV MPLBACKEND=Agg
# Imports use `from services...` with working directory `app/`
ENV PYTHONPATH=/app/app

WORKDIR /app/app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:5000/api/health || exit 1

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "main:app"]
