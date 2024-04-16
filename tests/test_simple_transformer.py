from mm.transformers.SimpleTransformer import SimpleTransformer


#   config:
#     x2:
#       formula: "QUAD:LTUH:680:BCTRL"
#     x1:
#       formula: "LUME:MLFLOW:TEST_A"

pv_mapping = {"x2": {"formula": "A1+B1"}, "x1": {"formula": "B1"}}
symbol_list = ["A1", "B1"]


def test_simple_transformer():
    st = SimpleTransformer(pv_mapping, symbol_list)

    st.handler("A1", {"value": 1})
    st.handler("B1", {"value": 2})

    assert st.updated == True

    assert st.latest_transformed["x2"] == 3
    assert st.latest_transformed["x1"] == 2
