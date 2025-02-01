
FROM python:3.12

# Copy only requirements to cache them in docker layer:
WORKDIR /usr

# Usage: COPY [from, from, from, to]
COPY ["./", "./"]

# Set the python path:
ENV PYTHONPATH="$PYTHONPATH:${PWD}"

RUN pip install --upgrade pip && pip install poetry==1.8 --break components

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main


CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8081"]

EXPOSE 8081

