FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        cracklib-runtime \
        libcrack2 \
        libcrack2-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install pip
RUN pip install -r /requirements.txt
COPY ./app /app