FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl git \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

COPY . /app

RUN poetry install --no-root

RUN poetry run python script.py

VOLUME ["/app/dist"]

CMD ["tail", "-f", "/dev/null"]
