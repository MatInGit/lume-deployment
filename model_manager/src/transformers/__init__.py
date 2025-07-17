registered_transformers = {}

from .BaseTransformers import (
    CAImageTransfomer,
    PassThroughTransformer,
    SimpleTransformer,
)
from .CompoundTransformer import CompoundTransformer

registered_transformers["SimpleTransformer"] = SimpleTransformer
registered_transformers["CAImageTransfomer"] = CAImageTransfomer
registered_transformers["CompoundTransformer"] = CompoundTransformer
registered_transformers["PassThroughTransformer"] = PassThroughTransformer
