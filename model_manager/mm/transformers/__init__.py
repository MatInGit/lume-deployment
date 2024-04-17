registered_transformers = {}

from .BaseTransformers import SimpleTransformer
from .BaseTransformers import CAImageTransfomer

registered_transformers["SimpleTransformer"] = SimpleTransformer
registered_transformers["CAImageTransfomer"] = CAImageTransfomer
