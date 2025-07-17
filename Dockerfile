FROM python:3.11.8-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
RUN python -m pip install botorch tensorflow pydantic torch==2.6.0 --no-cache-dir

COPY requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt --no-cache-dir
# RUN pip install -i https://test.pypi.org/simple/ lume-deploy==0.1.3 --extra-index-url https://pypi.org/simple/ --no-cache-dir

COPY . /opt/deployment
# COPY build-info.json /opt/deployment/
WORKDIR /opt/deployment
RUN python -m pip install . --no-cache-dir
WORKDIR /opt/deployment
CMD pl -n $MODEL_NAME -v $MODEL_VERSION -r -e env.json && pl -n $MODEL_NAME -v $MODEL_VERSION -p -e env.json
# CMD tail -f /dev/null