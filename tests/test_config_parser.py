from model_manager.src.config.parser import ConfigParser
import logging
import pytest

@pytest.fixture
def make_config_parser():
    def _make_config_parser(filename):
        return ConfigParser(filename)
    return _make_config_parser

# before test we need to delete ./graph folder
import shutil
shutil.rmtree('./graphs', ignore_errors=True)

def test_parse(caplog, make_config_parser):
    caplog.set_level(logging.DEBUG)
    parser = make_config_parser('pv_mapping.yaml')
    config = parser.parse()
    logging.debug(config)
    config.draw_routing_graph()
    assert config is not None

def test_parse_nonstandard1(caplog, make_config_parser):
    caplog.set_level(logging.DEBUG)
    parser = make_config_parser('pv_mapping_nonstandard_1.yaml')
    config = parser.parse()
    logging.debug(config)
    config.draw_routing_graph()
    assert config is not None
    
def test_parse_nonstandard2(caplog, make_config_parser):
    caplog.set_level(logging.DEBUG)
    parser = make_config_parser('pv_mapping_nonstandard_2.yaml')
    config = parser.parse()
    logging.debug(config)
    config.draw_routing_graph()
    assert config is not None

