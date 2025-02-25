from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    computed_field,
)
import time
from model_manager.src.logging_utils import get_logger
from model_manager.src.transformers import BaseTransformer
from model_manager.src.interfaces import BaseInterface
from model_manager.src.model_utils import registered_model_getters
import os

logger = get_logger()


class Message(BaseModel):
    topic: Union[str, list[str]]
    source: str
    ## key: str made a mess of this by including a key, no need to include a key
    value: dict = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    # optional
    allow_unsafe: Optional[bool] = False

    @field_validator("topic")
    @classmethod
    def check_topic(cls, topic):
        if not isinstance(topic, (str, list)):
            raise ValueError("topic must be a string or list of strings")
        elif isinstance(topic, list):
            t_len = len(topic)
            if t_len == 0 or t_len > 1:
                raise ValueError("topic list must contain one element")
            else:
                return topic[0]
        else:
            return topic
    
    @field_validator("value")
    @classmethod
    def check_value(cls, value):
        if not isinstance(value, dict):
            if cls.allow_unsafe:
                logger.warning(f"allowing unsafe value {value}")
                return {"value": value}
            else:
                raise ValueError("value must be a dictionary")
        # structs must be
        # {name : {"value": value, "timestamp": timestamp, "metadata": metadata}} value is mandatory, timestamp is optional, metadata is optional
        # can have multiple structs in a dictionary {name1: struct1, name2: struct2}
        for key, struct in value.items():
            if not isinstance(struct, dict):
                raise ValueError("struct must be a dictionary")
            if "value" not in struct:
                raise ValueError("struct must contain a value")
            if "timestamp" in struct:
                if not isinstance(struct["timestamp"], (int, float)):
                    raise ValueError("timestamp must be an int or float")
            if "metadata" in struct:
                if not isinstance(struct["metadata"], dict):
                    raise ValueError("metadata must be a dictionary")
        return value

    @computed_field
    def keys(self) -> list[str]:
        return list(self.value.keys())

    @computed_field
    def values(self) -> list[Any]:
        return list(self.value.values())

    def __str__(self):
        return f"Message(topic={self.topic}, source={self.source}, value={self.value}, timestamp={self.timestamp})"

    def __repr__(self):
        return f"Message(topic={self.topic}, source={self.source}, value={self.value}, timestamp={self.timestamp})"
    
    def __eq__(self, value):
        # value timestamp source and topic must be the same
        if self.topic == value.topic and self.source == value.source and self.timestamp == value.timestamp and self.value == value.value:
            return True
        else:
            return False


class Observer(ABC):
    @abstractmethod
    def update(self, message: Message) -> Message:
        # all updates should return a message
        pass


class MessageBroker:
    def __init__(self):
        """initialize the message broker"""
        self._observers: Dict[str, list[Observer]] = {}
        self._stats = {}
        self.queue = []

    def attach(self, observer: Observer, topic: str | list[str]) -> None:
        """add observer to topic"""
        logger.debug(f"attaching {observer} to {topic}")

        if isinstance(topic, list):
            for t in topic:
                if t not in self._observers:
                    self._observers[t] = []
                self._observers[t].append(observer)

        else:
            if topic not in self._observers:
                self._observers[topic] = []
            self._observers[topic].append(observer)

    def detach(self, observer: Observer, topic: str | list[str]) -> None:
        """remove observer from topic, we will probably never use this"""

        if isinstance(topic, list):
            for t in topic:
                if t in self._observers:
                    self._observers[t].remove(observer)
        else:
            self._observers[topic].remove(observer)

    def notify(self, message: Message) -> None:
        """notify all observers of a message"""
        if message.topic in self._observers:
            logger.debug(f"notifying observers of {message}")
            for observer in self._observers[message.topic]:
                logger.debug(f"notifying {observer} of {message}")
                result = observer.update(message)
                if result is not None:
                    # if list of messages
                    if isinstance(result, list):
                        for r in result:
                            self.queue.append(r)
                    else:
                        self.queue.append(result)
        else:
            logger.error(f"no observers for {message.topic}")

    def get_stats(self):
        return self._stats
    
    def get_all(self) -> None:
        refresh_msg = Message(
            topic="get_all", source="clock", value={"dummy": {"value": 1}}
        )
        self.notify(refresh_msg)
        return None

    def parse_queue(self):
        queue_snapshot = self.queue.copy()
        for message in queue_snapshot:
            self.notify(message)
            self.queue.remove(message)
            logger.debug(f"queue length: {len(self.queue)}")
            logger.debug(f"queue: {self.queue}")


class TransformerObserver(Observer):
    def __init__(
        self, transformer: BaseTransformer, topic: str, unpack_output: bool = False
    ):
        """wraps around the transformer.handler method"""
        self.transformer = transformer
        self.topic = topic
        self.unpack_output = unpack_output

    def update(self, message: Message) -> Message | list[Message]:

        for key, value in message.value.items():
            self.transformer.handler(key, value)

        if self.transformer.updated:
            value = self.transformer.latest_transformed
            if self.unpack_output:
                for key, value in value.items():
                    if isinstance(value, dict) and "value" in value:
                        self.transformer.updated = False
                        return Message(
                            topic=self.topic, source=str(self), value={key: value}
                        )
                    elif isinstance(value, dict) and "value" not in value:
                        self.transformer.updated = False
                        return Message(
                            topic=self.topic,
                            source=str(self),
                            value={key: {"value": value}},
                        )
                    else:
                        self.transformer.updated = False
                        return Message(
                            topic=self.topic,
                            source=str(self),
                            value={key: {"value": value}},
                        )

            else:
                if not isinstance(value, dict):
                    raise ValueError(f"value must be a dictionary, got {value}")

                if isinstance(value, dict) and "value" in value:
                    self.transformer.updated = False
                    return Message(
                        topic=self.topic, source=str(self), value={"transformed": value}
                    )
                elif isinstance(value, dict) and "value" not in value:
                    self.transformer.updated = False
                    return Message(
                        topic=self.topic,
                        source=str(self),
                        value={"transformed": {"value": value}},
                    )
                else:
                    raise ValueError(f"value must be a dictionary, got {value}")


class InterfaceObserver(Observer):
    def __init__(self, interface: BaseInterface, topic: str, sanitise: bool = True):
        """wraps around the interface.put_many method"""
        self.interface: BaseInterface = interface
        self.topic: str = topic
        self.sanitise = sanitise

    def update(self, message: Message) -> Message | list[Message]:
        if message.topic == "get_all":
            messages = self.get_all()
            return messages
        else:
            logger.debug(f"updating {self} with {message}")
            if os.environ["PUBLISH"] == "True":
                self.interface.put_many(message.value)
            else:
                logger.warning("PUBLISH is set to False, this will not publish to the interface")

    def get(self, message: Message) -> list[Message]:
        """get a single variable from the interface"""
        messages = []
        for key in message.keys:
            key, value = self.interface.get(key)
            messages.append(
                Message(topic=self.topic, source=str(self), value={key: value})
            )
        return messages

    def get_all(self) -> list[Message]:
        """get all variables from the interface based on internal variable list"""
        messages = []
        for key in self.interface.variable_list:
            key, value = self.interface.get(key)
            if value is not None:
                messages.append(
                    Message(topic=self.topic, source=str(self), value={key: value})
                )
        return messages

    def get_many(self, message: Message) -> list[Message]:
        """get many variables from the interface"""
        keys, values = self.interface.get_many(message.value)

        messages = []
        for key, value in values.items():
            messages.append(
                Message(topic=self.topic, source=str(self), value={key: value})
            )
        return messages

    def put(self, message: Message) -> None:
        """put a single variable into the interface"""
        if not isinstance(message.value, dict):
            raise ValueError("message value must be a dictionary")

        for key, value in zip(message.keys, message.values):
            self.interface.put(key, value)

    def put_many(self, message: Message) -> None:
        """put many variables into the interface"""
        if not isinstance(message.value, dict):
            raise ValueError("message value must be a dictionary")
        self.interface.put_many(message.value)


class MockModel:
    def __init__(self):
        """placeholder for model"""

    def evaluate(self, value):
        """placeholder for model prediction"""
        return {"not_initialized": {"value": -99999999999}}

class ModelObserver(Observer):
    def __init__(self, model=None, config = None, topic: str = "model"):
        """wraps around the model.predict method"""
        self.model = model
        self.topic = topic
        self.config = config
        
        if self.model is None and self.config is not None:
            self.model = self.__get_model()
            if not hasattr(self.model, "evaluate"):
                raise ValueError("model must have a .evaluate() method")
        elif self.model is not None:
            self.model = model
        else:
            raise ValueError("model must be provided or a config to load a model")
        
    def __get_model(self):
        """load the model from the config"""
        if self.config["type"] == "mock":
            return MockModel()
        if self.config["type"] == "MlflowModelGetter":
            model_getter = registered_model_getters["mlflow"](self.config["args"]) # legacy name well make it consistent across the board in the future
            model = model_getter.get_model()
            # check model is not None
            if model is None:
                raise ValueError("model is None")
            return model

        else:
            raise ValueError(f"model type not recognised: {self.config['type']}")
        
    def update(self, message: Message) -> list[Message]:
        logger.debug(f"updating {self} with {message.value}")
        pred = self.model.evaluate(message.value)
        messages = []
        for key, value in pred.items():
            messages.append(
                Message(topic=self.topic, source=str(self), value={key: value})
            )
        return messages


# class GenericObserver(Observer):
#     def __init__(self, callback):
#         """wraps around the callback method, a catch all observer"""
#         self.callback = callback

#     def update(self, message: Message) -> None:
#         self.callback(message)
