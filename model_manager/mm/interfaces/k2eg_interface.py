import k2eg, os, uuid
from .BaseInterface import BaseInterface

_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["K2EG_PYTHON_CONFIGURATION_PATH_FOLDER"] = _dir
# executor = ThreadPoolExecutor(20)

# print(f"K2EG_PYTHON_CONFIGURATION_PATH_FOLDER: {os.environ['K2EG_PYTHON_CONFIGURATION_PATH_FOLDER']})")


class K2EGInterface(BaseInterface):
    def __init__(self, config):
        self.client = k2eg.dml("env", "app-test-3", group_name="mlflow-test")

        pv_dict= config.config['variables']
        pv_url_list = []
        for pv in pv_dict:
            pv_url_list.append(pv_dict[pv]["proto"] + "://" + pv_dict[pv]["name"])
        self.pv_url_list = pv_url_list
        
    def monitor(self, handler, **kwargs):
        print(__name__ + "monitor")
        try:
            self.client.monitor_many(self.pv_url_list, handler, timeout=1000)
        except Exception as e:
            print(f"Error monitoring: {e}")
            raise e

    def get(self, name, **kwargs):
        return self.client.get(name)

    def put(self, name, value, **kwargs):
        self.client.put(name, value)

    def put_many(self, data, **kwargs):
        pass

    def get_many(self, data, **kwargs):
        pass
