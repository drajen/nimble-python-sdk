#
#   © Copyright 2020 Hewlett Packard Enterprise Development LP
#
#   This file was auto-generated by the Python SDK generator; DO NOT EDIT.
#

from ..resource import Resource, Collection
from ..exceptions import NimOSAPIOperationUnsupported

class FibreChannelPort(Resource):
    """
    Fibre Channel ports provide data access. This API provides the list of all Fibre Channel ports configured on the arrays.

    Parameters:
    - id                   : Identifier for the Fibre Channel port.
    - array_name_or_serial : Name or serial number of the array.
    - controller_name      : Name (A or B) of the controller to which the port belongs.
    - fc_port_name         : Name of the Fibre Channel port.
    - bus_location         : PCI bus location of the HBA (Host Bus Adapter) for this Fibre Channel port.
    - port                 : HBA (Host Bus Adapter) port number for this Fibre Channel port.
    - slot                 : HBA (Host Bus Adapter) slot number for this Fibre Channel port.
    - orientation          : Orientation of FC ports on a HBA. An orientation of 'right_to_left' indicates that ports are ordered as 3,2,1,0 on the slot. Possible values: 'left_to_right', 'right_to_left'.
    - link_info            : Information about the Fibre Channel link associated with this port.
    - rx_power             : SFP RX power in uW.
    - tx_power             : SFP TX power in uW.
    """

    def create(self, **kwargs):
        raise NimOSAPIOperationUnsupported("create operation not supported")

    def delete(self, **kwargs):
        raise NimOSAPIOperationUnsupported("delete operation not supported")

    def update(self, **kwargs):
        raise NimOSAPIOperationUnsupported("update operation not supported")

class FibreChannelPortList(Collection):
    resource = FibreChannelPort
    resource_type = "fibre_channel_ports"

    def create(self, **kwargs):
        raise NimOSAPIOperationUnsupported("create operation not supported")

    def delete(self, **kwargs):
        raise NimOSAPIOperationUnsupported("delete operation not supported")

    def update(self, **kwargs):
        raise NimOSAPIOperationUnsupported("update operation not supported")
