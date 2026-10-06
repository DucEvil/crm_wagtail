FROM apache/superset:6.0.0

USER root
RUN . /app/.venv/bin/activate && uv pip install psycopg2-binary==2.9.11
USER superset
