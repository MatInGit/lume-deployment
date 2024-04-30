FROM python:3.11.8-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
RUN python -m pip install botorch tensorflow --no-cache-dir

COPY requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt --no-cache-dir

COPY . /opt/deployment/
WORKDIR /opt/deployment/model_manager   
RUN python -m pip install -e . --no-cache-dir
WORKDIR /opt/deployment
CMD model_manager -n $model_name -v $model_version -r && model_manager -n $model_name -v $model_version -p
# CMD tail -f /dev/null