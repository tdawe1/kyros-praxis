FROM python:3.12-slim
WORKDIR /app
COPY main.py /app/main.py
ENV PYTHONUNBUFFERED=1 \
    KYROS_API_BASE=http://kyros_orchestrator:8000 \
    KYROS_REGISTRY_URL=http://kyros_registry:9000 \
    KYROS_DAEMON_URL=ws://kyros_daemon:8080/ws \
    QDRANT_URL=http://qdrant:6333 \
    KYROS_MCP_TOOLS=runs,registry,memory,terminal
CMD ["python","/app/main.py"]

