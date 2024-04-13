FROM python:3.11.8-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
RUN python -m pip install botorch tensorflow --no-cache-dir

COPY requirements.txt /opt/prefect/flow_prototype/requirements.txt
RUN python -m pip install -r /opt/prefect/flow_prototype/requirements.txt --no-cache-dir
ARG BUILD_NUMBER
COPY . /opt/deployment/
WORKDIR /opt/deployment/
CMD ["python", "entrypoint.py"]
