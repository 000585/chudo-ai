FROM python:3.12-slim as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y gcc libpq-dev
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
RUN apt-get update && apt-get install -y libpq5 postgresql-client redis-tools curl

COPY --from=builder /root/.local /root/.local
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./static ./static
COPY alembic.ini .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
