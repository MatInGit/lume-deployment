import pytest
from model_manager.src.utils.messaging import (
    Message,
    ModelObserver,
    InterfaceObserver,
    MessageBroker,
    TransformerObserver,
)
from model_manager.src.transformers.BaseTransformers import SimpleTransformer
from model_manager.src.interfaces import registered_interfaces

class MockModel:
    def __init__(self):
        self.predictions = []

    def predict(self, value):
        # add x1 and x2
        return {"pred": value['x1'] + value['x2']}

@pytest.fixture
def message_broker():
    return MessageBroker()

@pytest.fixture
def mock_model():
    return MockModel()

@pytest.fixture
def p4p_server():
    config = {
        'variables': {
            'A1': {
                'name': 'A1',
                'proto': 'pva',
                'type': 'scalar',
                'default': 2.0
            },
            'B1': {
                'name': 'B1',
                'proto': 'pva',
                'type': 'scalar',
                'default': 1.0
            },
        }
    }
    p4p = registered_interfaces['p4p_server'](config)
    yield p4p
    p4p.close()
    
    
@pytest.fixture
def model_observer(mock_model):
    return ModelObserver(mock_model, "model_out")

@pytest.fixture
def interface_observer(p4p_server):
    return InterfaceObserver(p4p_server, "in_interface")

@pytest.fixture
def transformer_observer():
    
    config1 = {
        'variables': {'x2': {'formula': 'A1 + B1'}, 'x1': {'formula': 'A1'}},
        'symbols': ['A1', 'B1'],
    }
    return TransformerObserver(SimpleTransformer(config1), "in_transformer")

# we want to test if the data goes from interface -> transformer -> model

def test_interface_observer_put(interface_observer, transformer_observer, model_observer, message_broker):
    # Broker setup 
    message_broker.attach(interface_observer, "get_all")
    message_broker.attach(transformer_observer, "in_interface")
    message_broker.attach(model_observer, "in_transformer")

    
    # get_all
    message = Message(topic="get_all", source="get_all", key="key", value=None)
    
    # this should trigger the interface to get all variables
    message_broker.notify(message)
    assert len(message_broker.queue) == 2
    for message in message_broker.queue:
        assert message.topic == "in_interface"
    message_broker.parese_queue()
    assert len(message_broker.queue) == 1
    assert message_broker.queue[0].topic == "in_transformer"
    message_broker.parese_queue()
    assert len(message_broker.queue) == 1
    assert message_broker.queue[0].topic == "model_out"