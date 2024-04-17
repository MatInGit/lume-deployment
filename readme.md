## Purpose and Idea
The purposue of the model manager is to allow for easy deployment of models from mlflow or other source (soon tm). 
The package is in an early stage and right now is tightly coupled with MLflow. The goal is to make it more general and allow for easy deployment of models from other sources as well. It should also account for different workflow types.

The idea is to divide model deployment into 3 stages 

### System level 
This stage we get the data from X system (in our case EPICS), this is where we are "relaxed" about the defintion of the data format. We just want to get the data and store it as a dictionary And supply it to a handler function.

Example
```python
my_data_getter.get(name:str) -> Tuple(key: str, value: Dict[str, Any])
```
or get many
```python
my_data_getter.get_many(names:List[str]) -> List[Tuple(key: str, value: Dict[str, Any])]
```
Note: this is only partially implemeted thats why `main()` uses `.get()` instead of `.get_many()`

Since we are focused on continuous data we also usualy have a monitor that calls a callback function when new data is available:

```python
my_data_getter.monitor(callback: Callable[[Dict[str, Any]], None])
```

### Transformation level
This is where we transform the data into a format that the model can understand; its where we are stricter about the data format.

Again since the initial focus was on continuous data, the transformer supplies a callback function that is called from the system level monitor function.

```python
my_transformer.handle(data: Dict[str, Any]) -> Dict[str, Any]
```
Now internaly the model tracks the lates input data, on each call to `handle` it updates the internal state and returns the transformed data.

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
# x should bea  dictionary with the transformed data, ready to be fed to the model
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
and done, now we follow the same pattern as before, model calls the callback function when new data is available.

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
## Available modules

TODO

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


## Usage

```bash


model_manager -n <model_name> -v <model_version> -e <env.json> -c <pv_mappings.yaml>
```