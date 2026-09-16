FROM secureintelligent/acp:latest

WORKDIR /app

RUN mkdir -p /app/incident

COPY collector_note.txt proxy_access.log app.jsonl app_audit_recovered.jsonl auth.log \
    edge_decisions.log edge_decisions_fragment.log dns_ptr_hints.txt /app/incident/

RUN chmod -R a+rX /app/incident
