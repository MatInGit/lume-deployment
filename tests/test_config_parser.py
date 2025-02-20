from model_manager.src.config.parser import ConfigParser
import logging

def test_parse(caplog):
    caplog.set_level(logging.DEBUG)
    parser = ConfigParser('pv_mapping.yaml')
    config = parser.parse()
    logging.debug(config)
    config.draw_routing_graph()
    assert config is not None


# def test_parse_nonstandard(caplog):
#     caplog.set_level(logging.DEBUG)
#     parser = ConfigParser('pv_mapping_nonstandard.yaml')
#     config = parser.parse()
#     logging.debug(config)
#     config.draw_routing_graph()
#     assert config is not None
