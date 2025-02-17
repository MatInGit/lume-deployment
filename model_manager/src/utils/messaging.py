from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field
import time
from model_manager.src.logging_utils import get_logger
from model_manager.src.transformers import BaseTransformer
from model_manager.src.interfaces import BaseInterface
import os

logger = get_logger()


class Message(BaseModel):
    topic: str
    source: str
    key: str
    value: Any
    timestamp: float = Field(default_factory=time.time)

    def __str__(self):
        return f"Message(topic={self.topic}, source={self.source}, key={self.key}, value={self.value}, timestamp={self.timestamp})"

    def __repr__(self):
        return f"Message(topic={self.topic}, source={self.source}, key={self.key}, value={self.value}, timestamp={self.timestamp})"


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
            for observer in self._observers[message.topic]:
                self.queue.append(observer.update(message))
        else:
            logger.error(f"no observers for {message.topic}")

    def get_stats(self):
        return self._stats

    def parese_queue(self):
        queue_snapshot = self.queue.copy()
        for message in queue_snapshot:
            self.notify(message)
            self.queue.remove(message)
            print(self.queue)


class TransformerObserver(Observer):
    def __init__(self, transformer: BaseTransformer, topic: str):
        """wraps around the transformer.handler method"""
        self.transformer = transformer
        self.topic = topic

    def update(self, message: Message) -> Message:
        self.transformer.handler(message.key, message.value)
        if self.transformer.updated:
            return Message(
                topic=self.topic,
                source=message.topic,
                key=message.key,
                value=self.transformer.latest_input,
            )


class InterfaceObserver(Observer):
    def __init__(self, interface: BaseInterface, topic: str):
        """wraps around the interface.put_many method"""
        self.interface = interface
        self.topic = topic

    def update(self, message: Message) -> None:
        if os.environ['PUBLISH'] == 'True':
            self.interface.put_many({message.key: message.value})
            
    def get(self, message: Message) -> None:
        """get a single variable from the interface"""
        _, value = self.interface.get(message.key)
        
        if value is not None:
            return Message(
                topic=self.topic,
                source='interface',
                key=message.key,
                value=value
            )
    
    def get_all(self) -> None:
        """get all variables from the interface based on internal variable list"""
        for key in self.interface.variable_list:
            _, value = self.interface.get(key)
        
            if value is not None:
                return Message(
                    topic=self.topic,
                    source='interface',
                    key=key,
                    value=value
                )        

    def put(self, message: Message) -> None:
        """put a single variable into the interface"""
        self.interface.put(message.key, message.value)

    def put_many(self, message: Message) -> None:
        """put many variables into the interface"""
        self.interface.put_many(message.value)

# class ModelObserver(Observer):
#     def __init__(self, model):
#         """wraps around the model.predict method"""
#         self.model = model

#     def update(self, message: Message) -> None:
#         self.model.predict(message.value)

# class GenericObserver(Observer):
#     def __init__(self, callback):
#         """wraps around the callback method, a catch all observer"""
#         self.callback = callback

#     def update(self, message: Message) -> None:
#         self.callback(message)
