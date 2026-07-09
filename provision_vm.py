from extras.scripts import Script, StringVar, ObjectVar, IntegerVar, BooleanVar, IPAddressWithMaskVar, TextVar
from virtualization.models import VirtualMachine, Cluster, VMInterface
from ipam.models import IPAddress
from dcim.models import Site, DeviceRole
from tenancy.models import Tenant


class CreateVM(Script):
    class Meta:
        name = "Create Virtual Machine"
        description = "Create a new virtual machine with network interface and IP address"
        commit_default = True

    # VM variables
    vm_name = StringVar(
        description="Virtual machine name",
        required=True
    )

    vm_description = TextVar(
        description="VM description",
        required=False
    )

    cluster = ObjectVar(
        model=Cluster,
        description="Cluster to assign the VM",
        required=True
    )

    site = ObjectVar(
        model=Site,
        description="Site location",
        required=False
    )

    role = ObjectVar(
        model=DeviceRole,
        description="VM role",
        required=False
    )

    tenant = ObjectVar(
        model=Tenant,
        description="Tenant",
        required=False
    )

    vcpus = IntegerVar(
        description="Number of vCPUs",
        default=2,
        required=False
    )

    memory = IntegerVar(
        description="Memory in MB",
        default=4096,
        required=False
    )

    disk = IntegerVar(
        description="Disk size in GB",
        default=50,
        required=False
    )

    # Interface variables
    interface_name = StringVar(
        description="Interface name (e.g., eth0)",
        default="eth0",
        required=True
    )

    interface_description = StringVar(
        description="Interface description",
        required=False
    )

    interface_enabled = BooleanVar(
        description="Enable interface",
        default=True
    )

    interface_mtu = IntegerVar(
        description="MTU size",
        default=1500,
        required=False
    )

    # IP address variables
    ip_address = IPAddressWithMaskVar(
        description="IP address with mask (e.g., 192.168.1.10/24)",
        required=True
    )

    ip_description = StringVar(
        description="IP address description",
        required=False
    )

    set_as_primary = BooleanVar(
        description="Set as primary IPv4 address",
        default=True
    )

    def run(self, data, commit):
        # Create the VM
        vm = VirtualMachine(
            name=data['vm_name'],
            description=data.get('vm_description', ''),
            cluster=data['cluster'],
            site=data.get('site'),
            role=data.get('role'),
            tenant=data.get('tenant'),
            vcpus=data.get('vcpus'),
            memory=data.get('memory'),
            disk=data.get('disk')
        )
        vm.save()
        self.log_success(f"Created virtual machine: {vm.name}")

        # Create interface for the VM
        interface = VMInterface(
            virtual_machine=vm,
            name=data['interface_name'],
            description=data.get('interface_description', ''),
            enabled=data.get('interface_enabled', True),
            mtu=data.get('interface_mtu')
        )
        interface.save()
        self.log_success(f"Created interface: {interface.name} on {vm.name}")

        # Create IP address and assign to interface
        ip = IPAddress(
            address=data['ip_address'],
            description=data.get('ip_description', ''),
            assigned_object=interface,
            tenant=data.get('tenant')
        )
        ip.save()
        self.log_success(f"Created IP address: {ip.address} on {interface.name}")

        # Set as primary IP if requested
        if data.get('set_as_primary', True):
            if ip.family == 4:
                vm.primary_ip4 = ip
            elif ip.family == 6:
                vm.primary_ip6 = ip
            vm.save()
            self.log_success(f"Set {ip.address} as primary IP for {vm.name}")

        return f"Successfully created VM: {vm.name} with interface: {interface.name} and IP: {ip.address}"
