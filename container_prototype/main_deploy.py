from model_utils.utils import MLflowModelGetter, VaraibleTransformer
import os, json, time
from k2eg_utils.utils import monitor, initialise_k2eg
import sys, time
import torch
import logging, psutil

# thread executor
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(20)
# logging.basicConfig(
#             format="[%(asctime)s %(levelname)-8s] %(message)s",
#             level=logging.DEBUG,
#         )

_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["K2EG_PYTHON_CONFIGURATION_PATH_FOLDER"] = os.path.join(_dir, "k2eg_utils")

model_getter = MLflowModelGetter(
    model_name=os.environ["model_name"], model_version=os.environ["model_version"]
)  # these will be grabbed from the environment variables

model = model_getter.get_model()
pv_mapping = model_getter.get_pv_mapping()
vt = VaraibleTransformer(pv_mapping["epics_to_model"], pv_mapping["epics_vars"].keys())
vto = VaraibleTransformer(pv_mapping["model_to_epics"], pv_mapping["model_output"])


publish = True

# it may not exist
if "deployment_publish" in model_getter.tags and model_getter.tags["deployment_publish"] is not None:
    if model_getter.tags["deployment_publish"].lower() == "false":
        publish = False
    elif model_getter.tags["deployment_publish"].lower() == "true":
        publish = True
    else:
        publish = False # value not recognised

print(f"Publishing: {publish}")

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

def put(k_out, key, value):
    try:
        res = k_out.put("pva://" + key, value, 10)
    except Exception as e:
        print(f"An error occured: {e}")
        res = f"An error occured: {e}"
        
    return res
input_stats = [0.0]
output_stats = [0.0]
def main():
    try:
        # returns mlflow.pyfunc.PyFuncModel
        print("initialising k2eg")
        k = initialise_k2eg(name = "app-test-3",group = str(os.environ["model_name"]+str(os.environ["model_version"])+"-input"))
        k_out = initialise_k2eg(name = "app-test-4" ,group = str(os.environ["model_name"]+str(os.environ["model_version"])+"-output"))
        print("k2eg initialised")

        # intialise pv values this section could be wrapped up in the vt module in the future
        print(f"Initialising PVs {pv_list}")
        
        for pv in pv_list:
            pv_full = k.get(pv)
            # print(f"PV: {pv}, Value: {val}")
            vt.handler_for_k2eg(pv, pv_full)

        monitor(pv_list=pv_list, handler=vt.handler_for_k2eg, client=k) # this doesnt need to be a sublclass given how simple it is
        time_update_stats = time.time()
        while True:
            if time.time() - time_update_stats > 1:
                metric_input = sum(input_stats)/len(input_stats) # mean of the last 3 times to get inputs 
                metric_output_total = sum(output_stats)/len(output_stats) # mean of the last 3 times to get outputs
                items = len(vto.latest_pvs.items())
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                handler_time = sum(vt.handler_time)/len(vt.handler_time)
                # format so that there are 10 spaces within which each stat can fit
                # | input_get: 0.12345 ms | output_put: 0.12345 ms | items: 123 | cpu: 12.34% | memory: 12.34% |
                print(f"| epics_to_handler {handler_time*1000:.5f} ms | input_process: {metric_input*1000:.5f} ms | output_put: {metric_output_total*1000:.5f} ms | items: {items} | cpu: {cpu:.2f}% | memory: {memory:.2f}% | {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} |")            
                
                # print(f"Inference time: {sum(input_stats)/len(input_stats)} sec, Output stats per item: {sum(output_stats)/len(output_stats)/len(vto.latest_pvs.items())} sec/item")
                time_update_stats = time.time()
            if vt.updated:
                time_start = time.time()
                inputs = vt.latest_transformed
                # print(f"Inputs: {inputs}")

                if model_getter.model_type == "torch":
                    for key, value in inputs.items():
                        inputs[key] = torch.tensor(
                            value, dtype=torch.float32
                        )  # this could be wrapped up in the vt module in the future

                output = model.evaluate(inputs)
                time_end = time.time()
                input_stats.append(time_end - time_start)
                if len(input_stats) > 3:
                    input_stats.pop(0)

                for key, value in output.items():
                    vto.handler_for_k2eg(key, {"value": value})

                if vto.updated and publish:
                    time_start = time.time()
                    futures = []
                    # for key, value in vto.latest_transformed.items():
                    #     futures.append(executor.submit(put, k_out, key, value))
                    futures = [executor.submit(put, k_out, key, value) for key, value in vto.latest_transformed.items()]
                    results = [future.result() for future in futures] # fire and forget but wanna know if it fails
                    # might wanna do additional error handling here
                    time_end = time.time()
                    # print(f"Time taken to put: {time_end - time_start} - {(time_end - time_start)/(len(vto.latest_transformed)) })")
                    output_stats.append(time_end - time_start)
                    if len(output_stats) > 3:
                        output_stats.pop(0)
                        
                    vto.updated = False

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
    main()