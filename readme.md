## Purpose and Idea
The purpose of the model manager is to allow for easy deployment of models from MLflow or other sources (soon tm). 
The package is in an early stage and right now is tightly coupled with MLflow. The goal is to make it more general and allow for easy deployment of models from other sources as well.

The idea is to divide model deployment into 3 layers:

### System level 
In this stage we get the data from X system (in our case EPICS), this is where we are "relaxed" about the definition of the data format. We just want to get the data and store it as a dictionary And supply it to a handler function.

Example
```python
my_data_getter.get(name:str) -> Tuple(key: str, value: Dict[str, Any])
```
or get many
```python
my_data_getter.get_many(names:List[str]) -> List[Tuple(key: str, value: Dict[str, Any])]
```
Note: this is only partially implemeted thats why `main()` uses `.get()` instead of `.get_many()`

Since we are focused on continuous data we also usually have a monitor that calls a callback function when new data is available:

```python
my_data_getter.monitor(callback: Callable[[Dict[str, Any]], None])
```

### Transformation level
This is where we transform the data into a format that the model can understand; it is where we are stricter about the data format.

Again since the initial focus was on continuous data, the transformer supplies a callback function that is called from the system level monitor function.

```python
my_transformer.handle(data: Dict[str, Any]) -> Dict[str, Any]
```
Now internally the model tracks the late input data, on each call to `handle` it updates the internal state and returns the transformed data.

Example:
```python
# my pretend system has 3 inputs it provides, the inputs need some adjustments before they can be fed to the model
config = {
    "variables": {
        "x1": {
            "formula": "LUME:MLFLOW:TEST_A"
        },
        "x2": {
            "formula": "LUME:MLFLOW:TEST_B"
        },
        "x3": {
            "formula": "LUME:MLFLOW:TEST_C + LUME:MLFLOW:TEST_B"
        }
    },
    "symbols": ["LUME:MLFLOW:TEST_A", "LUME:MLFLOW:TEST_B", "LUME:MLFLOW:TEST_C"]
}

transformer = SimpleTransformer(config) # all variables intialy set to None

# now manually call the handle function
transformer.handle("LUME:MLFLOW:TEST_A", 1) # this should update the internal state but internal update should only happen once all variables are updated
transformer.handle("LUME:MLFLOW:TEST_B", 2) # still no update
transformer.handle("LUME:MLFLOW:TEST_C", 3) # now the internal state should be updated

transformer.updated # should be True

x = transformer.latest_transformed
# x should be a dictionary with the transformed data, ready to be fed to the model
# {
#     "x1": 1,
#     "x2": 2,
#     "x3": 5
# }

```
### Model level
This is where a lume model is used to make predictions. The model should be able to handle the transformed data and return a prediction.

```python

output = some_lume_model.evaluate(data: Dict[str, Any]) -> Dict[str, Any]
# say output is:
# {
#     "y": 0.5
# }
```
and done, now we follow the same pattern as before, the model calls the callback function when new data is available.

```python

config = {
    "variables": {
        "LUME:MLFLOW:TEST_Y": {
            "formula": "y"
        }
    },
    "symbols": ["LUME:MLFLOW:TEST_Y"]
}

reverse_transformer = ReverseTransformer(config) # all variables intialy set to None

reverse_transformer.handle("y", 0.5) 

reverse_transformer.updated # should be True

y = reverse_transformer.latest_transformed

# should return
# {
#     "LUME:MLFLOW:TEST_Y": 0.5
# }
```
Then we pass the data to the system level and we are done.
```python
my_data_outputter.put(data: Dict[str, Any])
```
or many
```python
my_data_outputter.put_many(data: List[Dict[str, Any]])
```

To summarise the data flow is as follows:
```
System level -> Transformation level -> Model level -> Transformation level -> System level
```
All of this happens in the `main()` function in `model_manager/mm/cli.py` under `setup()` and `model_main()` methods.

## Available modules

### System
Purpose of the system module is to provide a way to get data from a system. The system can be anything from a database to a file or a live data source like EPICS, kafka, etc.

| Module | Description | YAML configuration | Compatible with: |
| ------ | ----------- | ------------------ | --------------- |
| `p4p` | EPICS data source, must have an external EPICS server running. Note that SoftIOCPVA will not work with this module. | [config](#p4p-sample-configuration) | `SimpleTransformer`, `CompoundTransformer` |
| `p4p_server` | EPICS data source, host EPICS p4p server for specifed PVs | same [config](#p4p-sample-configuration) as `p4p`  as p4p | `SimpleTransformer`, `CompoundTransformer` |
| `k2eg` | Kafka to EPICS gateway, get data from Kafka and write it to EPICS | [config](#k2eg-sample-configuration) | `SimpleTransformer`, `CompoundTransformer` , `CAImageTransformer`* |


*`CAImageTransformer` untested, but compatible with `k2eg` ca protocol only


#### `p4p` Sample configuration
```yaml
input_data:
  get_method: "p4p"
  config:
    EPICS_PVA_NAME_SERVERS: "134.79.151.21:5169" # can be a space separated list
    variables:
      LUME:MLFLOW:TEST_B:
        proto: pva # supports pva only
        name: LUME:MLFLOW:TEST_B
      LUME:MLFLOW:TEST_A:
        proto: pva
        name: LUME:MLFLOW:TEST_A
```
#### `k2eg` Sample configuration
```yaml
input_data:
  get_method: "k2eg"
  config:
    variables:
      LUME:MLFLOW:TEST_B:
        proto: ca # supports ca or pva
        name: LUME:MLFLOW:TEST_B
      LUME:MLFLOW:TEST_A:
        proto: pva
        name: LUME:MLFLOW:TEST_A
```

### Transformation

Purpose of the transformation module is to provide a way to transform the data into a format that the model can understand. Minor transformation operations like scaling, normalizing, etc. can be done here.

| Module | Description | YAML configuration | Compatible with: |
| ------ | ----------- | ------------------ | --------------- |
| `SimpleTransformer` | Simple transformer that can be used to transform scalar values (ca or pv values that have a `value` field) | [config](#simpletransformer-sample-configuration) | `p4p`,`p4p_server`, `k2eg`|
| `CAImageTransformer` | Transformer that can be used to transform a triplet of an array, x and y ca values into a np array | [config](#caimagetransformer-sample-configuration) | `k2eg` ca only|
| `CompoundTransformer` | Compound transformer that can be used to have multuple transformers in parallel | [config](#compoundtransformer-sample-configuration) | `p4p`,`p4p_server`, `k2eg`|

#### `SimpleTransformer` Sample configuration
```yaml
input_data_to_model:
  type: "SimpleTransformer"
  config:
    symbols:
      - "LUME:MLFLOW:TEST_B"
      - "LUME:MLFLOW:TEST_A"
    variables:
      x2:
        formula: "LUME:MLFLOW:TEST_B"
      x1: 
        formula: "LUME:MLFLOW:TEST_A"
```
Two keywords expected in the configuration are `varaibles` where one must sepcify the a list of output variables of the transformer and their associated `formula`s (in the example its `x1` and `x2`). The formulas tell us how to transform the input data from the providers to get the model input. `symbols` will be variables gathered from one of the compatible system data providers. All are intialised as `None` and are populated first via `.get()` then `.monitor()` methods of the providers. On each change a transform is executed and the transfomer provides a dictonary of model inputs for example `{'x1':1.2,'x2':3.2}`. `formula` can be any valid [SymPy](https://www.sympy.org/en/index.html) expression.

#### `CAImageTransformer` Sample configuration
```yaml
input_data_to_model:
  type: "CAImageTransformer"
    config:
        variables:
        img_1:
            img_ch: "MY_TEST_CA"
            img_x_ch: "MY_TEST_CA_X"
            img_y_ch: "MY_TEST_CA_Y"
        img_2:
            img_ch: "MY_TEST_C2"
            img_x_ch: "MY_TEST_CA_X2"
            img_y_ch: "MY_TEST_CA_Y2"
```
The above provides a way to transform a triplet of an array, x and y ca values into a np array. The `img_ch` is the channel for the image array, `img_x_ch` is the x channel and `img_y_ch` is the y channel. The transformer will wait for all three channels to be updated before transforming the data. The output will be a dictionary with the keys being the `img_ch` and the values being the np array. The x and y channels are not returned `{img_1: np.array, img_2: np.array}`. where `np.array` is a 2D numpy array with shape `(x,y)`.

#### `CompoundTransformer` Sample configuration
```yaml
input_data_to_model:
  type: "CompoundTransformer"
  config:
    transformers:
      transformer_1:
        type: "SimpleTransformer"
        config:
          symbols:
            - "LUME:MLFLOW:TEST_B"
            - "LUME:MLFLOW:TEST_A"
          variables:
            x2:
              formula: "LUME:MLFLOW:TEST_B"
            x1: 
              formula: "LUME:MLFLOW:TEST_A"
      transformer_2:
        type: "CAImageTransfomer"
        config:
          variables:
            img_1:
                img_ch: "MY_TEST_CA"
                img_x_ch: "MY_TEST_CA_X"
                img_y_ch: "MY_TEST_CA_Y"
            img_2:
                img_ch: "MY_TEST_C2"
                img_x_ch: "MY_TEST_CA_X2"
                img_y_ch: "MY_TEST_CA_Y2"
```
Combines multiple transformers in parallel. The output will be a combined dictionary og model outputs . Example: `{'x1':1.2,'x2':3.2, img_1: np.array, img_2: np.array}`


### Model

## YAML configuration

TODO

## MLFlow configuration

TODO

## Accepted Model formats

TODO

## Installation

```bash
pip install -r requirements.txt

cd model_manager
pip install .
```
for development

```bash
pip install -r requirements.txt

cd model_manager
pip install -e .
```

Conda env coming soon

## Usage

```bash
model_manager -n <model_name> -v <model_version> -e <env.json> -c <pv_mappings.yaml>
```

## Deployment

TODO