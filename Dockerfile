FROM python:3.11.8-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends git iputils-ping curl
RUN python -m pip install botorch tensorflow pydantic --no-cache-dir

COPY requirements.txt /app/requirements.txt
RUN python -m pip install -r /app/requirements.txt --no-cache-dir
RUN pip install -i https://test.pypi.org/simple/ lume-deploy==0.1.3.dev10 --extra-index-url https://pypi.org/simple/ --no-cache-dir

COPY . /opt/deployment/
# WORKDIR /opt/deployment/model_manager   
# RUN python -m pip install -e . --no-cache-dir
WORKDIR /opt/deployment
CMD model_manager -n $MODEL_NAME -v $MODEL_VERSION -r -e env.json && model_manager -n $MODEL_NAME -v $MODEL_VERSION -p -e env.json
# CMD tail -f /dev/null