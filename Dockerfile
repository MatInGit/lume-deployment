# FROM python:3.11.8-slim-bullseye
# RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
# RUN python -m pip install botorch tensorflow pydantic torch==2.6.0 --no-cache-dir

# COPY requirements.txt /app/requirements.txt
# RUN python -m pip install -r /app/requirements.txt --no-cache-dir
# # RUN pip install -i https://test.pypi.org/simple/ lume-deploy==0.1.3 --extra-index-url https://pypi.org/simple/ --no-cache-dir

# COPY . /opt/deployment
# # COPY build-info.json /opt/deployment/
# WORKDIR /opt/deployment
# RUN python -m pip install . --no-cache-dir
# WORKDIR /opt/deployment
# CMD pl -n $MODEL_NAME -v $MODEL_VERSION -r -e env.json && pl -n $MODEL_NAME -v $MODEL_VERSION -p -e env.json
# # CMD tail -f /dev/null
# Stage 1: Base image with common dependencies

FROM python:3.11.8-slim-bullseye AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt --no-cache-dir


FROM base AS torch
# Install additional ML libraries
RUN python -m pip install botorch pydantic torch==2.6.0 --no-cache-dir
# need to copy poly_lithic, pyptoject.toml and tests
COPY poly_lithic /opt/poly_lithic
COPY pyproject.toml /opt/deployment/pyproject.toml
COPY tests /opt/deployment/tests
WORKDIR /opt/deployment
RUN python -m pip install poly-lithic --no-cache-dir

CMD pl -c config.yaml -r -e env.json && pl --publish -c config.yaml -e env.json

FROM base AS tensorflow
# Install additional ML libraries
RUN python -m pip install pydantic tensorflow --no-cache-dir

COPY poly_lithic /opt/poly_lithic
COPY pyproject.toml /opt/deployment/pyproject.toml
COPY tests /opt/deployment/tests
WORKDIR /opt/deployment
RUN python -m pip install poly-lithic --no-cache-dir

CMD pl -c config.yaml -r -e env.json && pl --publish -c config.yaml -e env.json


FROM base AS vanilla

COPY poly_lithic /opt/poly_lithic
COPY pyproject.toml /opt/deployment/pyproject.toml
COPY tests /opt/deployment/tests
WORKDIR /opt/deployment
RUN python -m pip install poly-lithic --no-cache-dir

CMD pl -c config.yaml -r -e env.json && pl --publish -c config.yaml -e env.json
