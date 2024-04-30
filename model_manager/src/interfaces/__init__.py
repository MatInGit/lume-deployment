registered_interfaces = {}

try:
    from .k2eg_interface import K2EGInterface

    registered_interfaces["k2eg"] = K2EGInterface
except ImportError as e:
    print(f"Error importing k2eg interface: {e}")
    raise e

try:
    from .p4p_interface import SimplePVAInterface
    from .p4p_interface import SimlePVAInterfaceServer

    registered_interfaces["p4p"] = SimplePVAInterface
    registered_interfaces["p4p_server"] = SimlePVAInterfaceServer
except ImportError as e:
    print(f"Error importing pva interface: {e}")
    raise e
    
try:
    from .file_interface import h5dfInterface

    registered_interfaces["h5df"] = h5dfInterface
except ImportError as e:
    print(f"Error importing h5df interface: {e}")
    raise e
