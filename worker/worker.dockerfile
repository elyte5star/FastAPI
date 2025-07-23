FROM python:3.12

WORKDIR /usr

COPY ["./", "./"]

# Set the python path:
ENV PYTHONPATH="$PYTHONPATH:${PWD}"

RUN pip install --upgrade pip && pip install -r requirements.txt


CMD ["python", "-u", "run_worker.py"]

