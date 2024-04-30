registered_model_getters = {}
# stole this way from lume model

# base class
from src.model_utils.ModelGetterBase import ModelGetterBase

try:
    from src.model_utils.MlflowModelGetter import MLflowModelGetter

    registered_model_getters["mlflow"] = MLflowModelGetter

except Exception as e:
    print(f"Error importing MLflowModelGetter: {e}")

try:
    from src.model_utils.LocalModelGetter import LocalModelGetter

    registered_model_getters["local"] = LocalModelGetter
except Exception as e:
    print(f"Error importing LocalModelGetter: {e}")
