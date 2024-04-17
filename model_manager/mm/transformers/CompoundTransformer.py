# defines a compound transformer that can be used add multiple transformers together
from mm.logging_utils.make_logger import get_logger
from mm.transformers import registered_transformers
import sympy as sp

logger = get_logger()


class CompoundTransformer:
    def __init__(self, config):
        logger.debug("Initializing CompoundTransformer")
        self.transformers = []
        for transformer in config["transformers"]:
            if transformer["name"] not in registered_transformers:
                raise Exception(
                    f"Transformer {transformer['name']} not found in registered_transformers, choose from {list(registered_transformers.keys())}"
                )
            else:
                logger.debug(f"Initializing {transformer['name']} transformer")
                self.transformers.append(
                    registered_transformers[transformer["name"]](
                        transformer["pv_mapping"], transformer
                    )
                )

    def transform(self, data):
        for transformer in self.transformers:
            data = transformer.transform(data)
        return data

    def __str__(self):
        return f"CompoundTransformer({', '.join([str(t) for t in self.transformers])})"

    def __repr__(self):
        return str(self)
