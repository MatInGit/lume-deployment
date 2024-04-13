registered_interfaces = {}

try:
    from .k2eg_interface import K2EGInterface

    registered_interfaces["k2eg"] = K2EGInterface
except ImportError as e:
    print(f"Error importing k2eg interface: {e}")
