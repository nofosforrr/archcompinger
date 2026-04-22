FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY archcompinger/ archcompinger/

RUN pip install --no-cache-dir .

CMD ["archcompinger"]
