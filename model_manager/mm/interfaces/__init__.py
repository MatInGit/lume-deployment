registered_interfaces = {}

try:
    from .k2eg_interface import K2EGInterface

    registered_interfaces["k2eg"] = K2EGInterface
except ImportError as e:
    print(f"Error importing k2eg interface: {e}")

try:
    from .p4p_interface import SimplePVAInterface
    from .p4p_interface import SimlePVAInterfaceServer

    registered_interfaces["p4p"] = SimplePVAInterface
    registered_interfaces["p4p_server"] = SimlePVAInterfaceServer
except ImportError as e:
    print(f"Error importing pva interface: {e}")
