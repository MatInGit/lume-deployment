from model_manager.src.model_utils.LocalModelGetter import LocalModelGetter


def test_LocalModelGetter():
    model_getter = LocalModelGetter(
        {
            "model_path": "tests/model/model_definition.py",
            "model_factory_class": "ModelFactory",
        }
    )
    model = model_getter.get_model()
    input_dict = {"x1": 1, "x2": 2}
    output_dict = model.evaluate(input_dict)
    assert output_dict["y"] == 2
