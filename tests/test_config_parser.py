from src.config.parser import ConfigParser


def test_parse():
    parser = ConfigParser("pv_mapping.yaml")
    config = parser.parse()
    assert config is not None
