# Dockerfile

FROM python:3.11
WORKDIR /app

# ----> THIS LINE IS CRITICAL <----
RUN apt-get update && apt-get install -y postgresql-client

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and the app code
COPY ./wait-for-postgres.sh /app/wait-for-postgres.sh
COPY ./app /app/app

EXPOSE 8000

# ----> THESE LINES ARE CRITICAL <----
ENTRYPOINT ["/app/wait-for-postgres.sh"]
CMD ["db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]