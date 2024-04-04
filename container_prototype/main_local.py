import os, json

json_data = json.load(open("cred.json"))

os.environ["MLFLOW_TRACKING_USERNAME"] = json_data["MLFLOW_TRACKING_USERNAME"]
os.environ["MLFLOW_TRACKING_PASSWORD"] = json_data["MLFLOW_TRACKING_PASSWORD"]
os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = json_data[
    "MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"
]
os.environ["AWS_DEFAULT_REGION"] = json_data["AWS_DEFAULT_REGION"]
os.environ["AWS_REGION"] = json_data["AWS_REGION"]
os.environ["AWS_ACCESS_KEY_ID"] = json_data["AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = json_data["AWS_SECRET_ACCESS_KEY"]
os.environ["MLFLOW_S3_ENDPOINT_URL"] = json_data["MLFLOW_S3_ENDPOINT_URL"]
# tracking uri
os.environ["MLFLOW_TRACKING_URI"] = json_data["MLFLOW_TRACKING_URI"]

os.environ["model_name"] = "lcls-cu-inj-nn"
os.environ["model_version"] = "champion"

import main_deploy

if __name__ == "__main__":
    main_deploy.main()
