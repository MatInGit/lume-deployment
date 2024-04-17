from mm.transformers.BaseTransformers import SimpleTransformer
from mm.logging_utils.make_logger import get_logger
import math
logger = get_logger()

config1 = {
    "variables": {"x2": {"formula": "A1 + B1"}, "x1": {"formula": "A1"}},
    "symbols": ["A1", "B1"],
}

def test_simple_transformer():
    st = SimpleTransformer(config1)

    print(st)
    print(st.pv_mapping)

    st.handler("A1", {"value": 1})
    st.handler("B1", {"value": 2})

    assert st.updated == True
    print(st.latest_transformed)

    assert st.latest_transformed["x2"] == 1 + 2
    assert st.latest_transformed["x1"] == 1


# more complex configuration
config2 = {
    "variables": {
        "x2": {"formula": "A1**2"},
        "x1": {"formula": "A1"},
        "x3": {"formula": "sin(A1) + cos(B1)"},
    },
    "symbols": ["A1", "B1"],
}



def test_simple_transformer_complex():
    st = SimpleTransformer(config2)

    print(st)
    print(st.pv_mapping)

    st.handler("A1", {"value": 1})
    st.handler("B1", {"value": 2})

    assert st.updated == True

    assert st.latest_transformed["x2"] == 1 ** 2
    assert st.latest_transformed["x1"] == 1
    assert st.latest_transformed["x3"] == math.sin(1) + math.cos(2)
