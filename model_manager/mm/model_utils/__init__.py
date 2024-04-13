registered_model_getters = {}
# stole this way from lume model

# base class
from mm.model_utils.ModelGetterBase import ModelGetterBase

try:
    from mm.model_utils.MlflowModelGetter import MLflowModelGetter

    registered_model_getters["mlflow"] = MLflowModelGetter

except Exception as e:
    print(f"Error importing MLflowModelGetter: {e}")

try:
    from mm.model_utils.LocalModelGetter import LocalModelGetter

    registered_model_getters["local"] = LocalModelGetter
except Exception as e:
    print(f"Error importing LocalModelGetter: {e}")
