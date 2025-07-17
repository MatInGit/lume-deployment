from model_manager.src.model_utils.LocalModelGetter import LocalModelGetter
import cProfile
import os
def test_LocalModelGetter():
    model_getter = LocalModelGetter({
        'model_path': 'tests/model/model_definition.py',
        'model_factory_class': 'ModelFactory',
    })
    model = model_getter.get_model()
    input_dict = {'x1': 1, 'x2': 2}
    
    for  i in range(10):
        input_dict['x1'] = i
        input_dict['x2'] = i*2
        output_dict = model.evaluate(input_dict)
        assert output_dict['y'] == max(input_dict['x1'], input_dict['x2'])
# def test_profile():
#     # Use runctx instead of run to provide the globals/locals context
#     cProfile.runctx('test_LocalModelGetter()', globals(), locals(), 'tests/test_LocalModelGetter.prof')
#     os.system('flameprof tests/test_LocalModelGetter.prof > tests/test_LocalModelGetter_flamegraph.html')
# not particularly useful for this test case, but can be useful for more complex test cases