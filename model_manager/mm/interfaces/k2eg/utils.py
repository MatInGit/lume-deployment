import k2eg
import os
import uuid

# needs to be removed in the future versions as this wrapper doesnt add any value


def initialise_k2eg(name="app-test-3", group="test"):
    """Initialise a K2EG client
    Returns:
        k2eg: K2EG client
    """
    k = k2eg.dml("env", name, group_name=group)
    return k


def monitor(pv_list: list, handler: callable, client: k2eg.dml, timeout=10):
    """Monitor a list of PVs with a handler function
    Args:
        pv_list (list): List of PVs to monitor
        handler (callable): Function to handle the PV data
        client (k2eg, optional): K2EG client.
    """
    client.monitor_many(pv_list, handler, timeout=timeout)
