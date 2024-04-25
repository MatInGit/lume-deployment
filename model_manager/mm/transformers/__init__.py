registered_transformers = {}

from .BaseTransformers import SimpleTransformer
from .BaseTransformers import CAImageTransfomer
from .CompoundTransformer import CompoundTransformer

registered_transformers["SimpleTransformer"] = SimpleTransformer
registered_transformers["CAImageTransfomer"] = CAImageTransfomer
registered_transformers["CompoundTransformer"] = CompoundTransformer
