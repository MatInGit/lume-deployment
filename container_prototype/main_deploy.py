from model_utils.utils import MLflowModelGetter, VaraibleTransformer
import os, json, time
from k2eg_utils.utils import monitor, initialise_k2eg
import sys, time
import torch
import logging 
# logging.basicConfig(
#             format="[%(asctime)s %(levelname)-8s] %(message)s",
#             level=logging.DEBUG,
#         )

_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["K2EG_PYTHON_CONFIGURATION_PATH_FOLDER"] = os.path.join(_dir, "k2eg_utils")


print(os.environ["K2EG_PYTHON_CONFIGURATION_PATH_FOLDER"])


model_getter = MLflowModelGetter(
    model_name=os.environ["model_name"], model_version=os.environ["model_version"]
)  # these will be grabbed from the environment variables

model = model_getter.get_model()
pv_mapping = model_getter.get_pv_mapping()
vt = VaraibleTransformer(pv_mapping["epics_to_model"], pv_mapping["epics_vars"].keys())
vto = VaraibleTransformer(pv_mapping["model_to_epics"], pv_mapping["model_output"])

pv_list = []
pv_list_output = []

for key, value in pv_mapping[
    "epics_vars"
].items():  # this could be wrapped up in the vt module in the future
    pv_list.append(value["source"])

for key in pv_mapping[
    "model_to_epics"
].keys():
    pv_list_output.append("pva://"+ key)


def main():
    try:
        # returns mlflow.pyfunc.PyFuncModel
        print("initialising k2eg")
        k = initialise_k2eg()
        k_out = initialise_k2eg(name = "app-test-4")
        print("k2eg initialised")

        # intialise pv values this section could be wrapped up in the vt module in the future
        for pv in pv_list:
            pv_full = k.get(pv)
            val = pv_full["value"]
            # print(f"PV: {pv}, Value: {val}")
            vt.handler_for_k2eg(pv, pv_full)

        monitor(pv_list=pv_list, handler=vt.handler_for_k2eg, client=k) # this doesnt need to be a sublclass given how simple it is

        while True:
            if vt.updated:
                inputs = vt.latest_transformed
                # print(f"Inputs: {inputs}")

                if model_getter.model_type == "torch":
                    for key, value in inputs.items():
                        inputs[key] = torch.tensor(
                            value, dtype=torch.float32
                        )  # this could be wrapped up in the vt module in the future

                output = model.evaluate(inputs)

                for key, value in output.items():
                    vto.handler_for_k2eg(key, {"value": value})

                if vto.updated:
                    time_start = time.time()
                    for key, value in vto.latest_transformed.items():
                        # print(f"Output: {key}, Value: {value}")
                        try:
                            k_out.put("pva://" + key, value, 1)
                        except Exception as e:
                            print(f"An error occured: {e}")
                    time_end = time.time()
                    print(f"Time taken to put: {time_end - time_start} - {(time_end - time_start)/len(vto.latest_transformed) })")


                # print(f"Output: {output}")
                vt.updated = False

    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
        print("Closing k2eg")
        k.close()
        k_out.close()
        print("Exiting...")
        raise KeyboardInterrupt

    except Exception as e:
        print(f"An error occured: {e}")
        print("Closing k2eg")
        k.close()
        k_out.close()
        print("Exiting...")
        raise e


if __name__ == "__main__":
    print("Starting the main_deploy script...")
    main()
