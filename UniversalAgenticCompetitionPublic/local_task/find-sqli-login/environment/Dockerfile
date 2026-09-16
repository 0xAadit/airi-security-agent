FROM secureintelligent/acp:latest

RUN apt-get update && \
    apt-get install -y postgresql && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ .
RUN /app/.venv/bin/uv pip install --python /app/.venv/bin/python .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
