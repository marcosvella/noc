# ---------------------------------------------------------------------
# Interface check
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from collections import defaultdict

# Third-party modules
from typing import Dict

# NOC modules
from noc.core.text import ranges_to_list
from noc.services.discovery.jobs.base import PolicyDiscoveryCheck
from noc.core.vpn import get_vpn_id
from noc.core.service.rpc import RPCError
from noc.inv.models.forwardinginstance import ForwardingInstance
from noc.inv.models.interface import Interface
from noc.inv.models.interfaceprofile import InterfaceProfile
from noc.inv.models.subinterface import SubInterface
from noc.inv.models.interfaceclassificationrule import InterfaceClassificationRule
from noc.sa.interfaces.igetinterfaces import IGetInterfaces


class InterfaceCheck(PolicyDiscoveryCheck):
    """
    Version discovery
    """

    name = "interface"
    required_script = "get_interfaces"

    IF_QUERY = """(
        Match("interfaces", if_name) or
        Match("interfaces", if_name, "type", type) or
        Match("interfaces", if_name, "description", description) or
        Match("interfaces", if_name, "admin-status", admin_status)
    ) and Group("if_name")"""

    UNIT_QUERY = """(
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit) or
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit, "description", description) or
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit, "inet", "address", ipv4_addresses) or
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit, "inet6", "address", ipv6_addresses) or
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit, "bridge", "switchport", "tagged", tagged) or
        Match("virtual-router", vr, "forwarding-instance", instance, "interfaces", if_name, "unit", unit, "bridge", "switchport", "untagged", untagged)
    ) and Group("vr", "instance", "if_name", "unit", stack={"ipv4_addresses", "ipv6_addresses"})"""

    VRF_QUERY = """(Match("virtual-router", vr, "forwarding-instance", instance) or
        Match("virtual-router", vr, "forwarding-instance", instance, "type", type) or
        Match("virtual-router", vr, "forwarding-instance", instance, "vpn-id", vpn_id) or
        Match("virtual-router", vr, "forwarding-instance", instance, "route-distinguisher", rd) or
        Match("virtual-router", vr, "forwarding-instance", instance, "vrf-target", "export", rt_export) or
        Match("virtual-router", vr, "forwarding-instance", instance, "vrf-target", "import", rt_import)
    ) and Group("vr", "instance", stack={"rt_export", "rt_import"})"""

    PROTOCOLS_QUERY = """(Match("protocols", "lldp", "interface", if_name, "admin-status", lldp_status) or
        Match("protocols", "spanning-tree", "interface", if_name, "admin-status", stp_status)
    ) and Group("if_name")"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_interface_profile = InterfaceClassificationRule.get_classificator()
        self.interface_macs = set()
        self.seen_interfaces = []
        self.vrf_artefact = {}  # name -> {name:, type:, rd:}
        self.prefix_artefact = {}
        self.interface_prefix_artefact = []

    def handler(self):
        self.logger.info("Checking interfaces")
        result = self.get_data()
        if not result:
            self.logger.error("Failed to get interfaces")
            return
        if_map: Dict[str, Interface] = {}
        # Process forwarding instances
        for fi in result:
            vpn_id = fi.get("vpn_id")
            # Apply forwarding instance
            forwarding_instance = self.submit_forwarding_instance(
                name=fi["forwarding_instance"],
                type=fi["type"],
                rd=fi.get("rd"),
                rt_export=fi.get("rt_export"),
                rt_import=fi.get("rt_import"),
                vr=fi.get("vr"),
                vpn_id=vpn_id,
            )
            # Move LAG members to the end
            # for effective caching
            ifaces = sorted(fi["interfaces"], key=self.in_lag)
            icache = {}
            for i in ifaces:
                # Get LAG
                agg = None
                if self.in_lag(i):
                    agg = icache.get(i["aggregated_interface"])
                    if not agg:
                        self.logger.error(
                            "Cannot find aggregated interface '%s'. " "Skipping %s",
                            i["aggregated_interface"],
                            i["name"],
                        )
                        continue
                # Submit discovered interface
                mac = i.get("mac")
                iface = self.submit_interface(
                    name=i["name"],
                    default_name=i.get("default_name"),
                    type=i["type"],
                    mac=mac,
                    description=i.get("description"),
                    aggregated_interface=agg,
                    enabled_protocols=i.get("enabled_protocols", []),
                    ifindex=i.get("snmp_ifindex"),
                    hints=i.get("hints", []),
                )
                icache[i["name"]] = iface
                # Submit subinterfaces
                for si in i["subinterfaces"]:
                    self.submit_subinterface(
                        forwarding_instance=forwarding_instance,
                        interface=iface,
                        name=si["name"],
                        description=si.get("description"),
                        mac=si.get("mac", i.get("mac")),
                        vlan_ids=si.get("vlan_ids", []),
                        enabled_afi=si.get("enabled_afi", []),
                        ipv4_addresses=si.get("ipv4_addresses", []),
                        ipv6_addresses=si.get("ipv6_addresses", []),
                        iso_addresses=si.get("iso_addresses", []),
                        vpi=si.get("vpi"),
                        vci=si.get("vci"),
                        enabled_protocols=si.get("enabled_protocols", []),
                        untagged_vlan=si.get("untagged_vlan"),
                        tagged_vlans=si.get("tagged_vlans", []),
                        # ip_unnumbered_subinterface
                        ifindex=si.get("snmp_ifindex"),
                    )
                    addresses = si.get("ipv4_addresses", []) + si.get("ipv6_addresses", [])
                    if addresses:
                        rd = forwarding_instance.rd if forwarding_instance else "0:0"
                        for a in addresses:
                            self.interface_prefix_artefact += [
                                {
                                    "vpn_id": vpn_id,
                                    "rd": rd,
                                    "address": a,
                                    "subinterface": si["name"],
                                    "description": si.get("description"),
                                    "mac": mac,
                                    "vlan_ids": si.get("vlan_ids", []),
                                }
                            ]
                # Delete hanging subinterfaces
                self.cleanup_subinterfaces(
                    forwarding_instance, iface, [si["name"] for si in i["subinterfaces"]]
                )
                # Perform interface classification
                self.interface_classification(iface)
                # Store for future collation
                if_map[iface.name] = iface
            # Delete hanging interfaces
            self.seen_interfaces += [i["name"] for i in fi["interfaces"]]
        # Delete hanging interfaces
        self.cleanup_interfaces(self.seen_interfaces)
        # Delete hanging forwarding instances
        self.cleanup_forwarding_instances(fi["forwarding_instance"] for fi in result)
        self.resolve_properties()
        self.update_caps(
            {"DB | Interfaces": Interface.objects.filter(managed_object=self.object.id).count()},
            source="interface",
        )
        #
        self.collate(if_map)
        # Set artifacts for future use
        self.set_artefact("interface_macs", self.interface_macs)
        self.set_artefact("interface_vpn", self.vrf_artefact)
        self.set_artefact("interface_prefix", self.interface_prefix_artefact)

    def submit_forwarding_instance(self, name, type, rd, rt_export, rt_import, vr, vpn_id=None):
        if name == "default":
            return None
        rt_export = rt_export or []
        rt_import = rt_import or []
        forwarding_instance = ForwardingInstance.objects.filter(
            managed_object=self.object.id, name=name
        ).first()
        if forwarding_instance:
            changes = self.update_if_changed(
                forwarding_instance,
                {
                    "type": type,
                    "name": name,
                    "vpn_id": vpn_id,
                    "rd": rd,
                    "rt_export": rt_export,
                    "rt_import": rt_import,
                },
            )
            self.log_changes("Forwarding instance '%s' has been changed" % name, changes)
        else:
            self.logger.info("Create forwarding instance '%s' (%s)", name, type)
            forwarding_instance = ForwardingInstance(
                managed_object=self.object.id,
                name=name,
                type=type,
                vpn_id=vpn_id,
                rd=rd,
                rt_export=rt_export,
                rt_import=rt_import,
                virtual_router=vr,
            )
            forwarding_instance.save()
        self.vrf_artefact[name] = {
            "name": name,
            "type": type,
            "rd": rd,
            "vpn_id": vpn_id,
            "rt_export": rt_export,
            "rt_import": rt_import,
        }
        return forwarding_instance

    def submit_interface(
        self,
        name,
        type,
        default_name=None,
        mac=None,
        description=None,
        aggregated_interface=None,
        enabled_protocols=None,
        ifindex=None,
        hints=None,
    ):
        enabled_protocols = enabled_protocols or []
        iface = self.get_interface_by_name(name)
        if iface:
            # Interface exists
            changes = self.update_if_changed(
                iface,
                {
                    "default_name": default_name,
                    "type": type,
                    "mac": mac,
                    "description": description,
                    "aggregated_interface": aggregated_interface,
                    "enabled_protocols": enabled_protocols,
                    "ifindex": ifindex,
                    "hints": hints or [],
                },
                ignore_empty=["ifindex"],
            )
            self.log_changes("Interface '%s' has been changed" % name, changes)
        else:
            # Create interface
            self.logger.info("Creating interface '%s'", name)
            iface = Interface(
                managed_object=self.object.id,
                name=name,
                type=type,
                mac=mac,
                description=description,
                aggregated_interface=aggregated_interface,
                enabled_protocols=enabled_protocols,
                ifindex=ifindex,
            )
            iface.save()
            self.set_interface(name, iface)
        if mac:
            self.interface_macs.add(mac)
        return iface

    def submit_subinterface(
        self,
        forwarding_instance,
        interface,
        name,
        description=None,
        mac=None,
        vlan_ids=None,
        enabled_afi=[],
        ipv4_addresses=[],
        ipv6_addresses=[],
        iso_addresses=[],
        vpi=None,
        vci=None,
        enabled_protocols=[],
        untagged_vlan=None,
        tagged_vlans=[],
        ifindex=None,
    ):
        mac = mac or interface.mac
        si = self.get_subinterface(interface, name)
        if si:
            changes = self.update_if_changed(
                si,
                {
                    "forwarding_instance": forwarding_instance,
                    "description": description,
                    "mac": mac,
                    "vlan_ids": vlan_ids,
                    "enabled_afi": enabled_afi,
                    "ipv4_addresses": ipv4_addresses,
                    "ipv6_addresses": ipv6_addresses,
                    "iso_addresses": iso_addresses,
                    "vpi": vpi,
                    "vci": vci,
                    "enabled_protocols": enabled_protocols,
                    "untagged_vlan": untagged_vlan,
                    "tagged_vlans": tagged_vlans,
                    # ip_unnumbered_subinterface
                    "ifindex": ifindex,
                },
                ignore_empty=["ifindex"],
            )
            self.log_changes("Subinterface '%s' has been changed" % name, changes)
        else:
            self.logger.info("Creating subinterface '%s'", name)
            si = SubInterface(
                forwarding_instance=forwarding_instance,
                interface=interface.id,
                managed_object=self.object.id,
                name=name,
                description=description,
                mac=mac,
                vlan_ids=vlan_ids,
                enabled_afi=enabled_afi,
                ipv4_addresses=ipv4_addresses,
                ipv6_addresses=ipv6_addresses,
                iso_addresses=iso_addresses,
                vpi=None,
                vci=None,
                enabled_protocols=enabled_protocols,
                untagged_vlan=untagged_vlan,
                tagged_vlans=tagged_vlans,
                ifindex=ifindex,
            )
            si.save()
        if mac:
            self.interface_macs.add(mac)
        return si

    def cleanup_forwarding_instances(self, fi):
        """
        Delete hanging forwarding instances
        :param fi: generator yielding instance names
        :return:
        """
        db_fi = set(
            i["name"]
            for i in ForwardingInstance.objects.filter(managed_object=self.object.id).only("name")
        )
        for i in db_fi - set(fi):
            self.logger.info("Removing forwarding instance %s", i)
            for dfi in ForwardingInstance.objects.filter(managed_object=self.object.id, name=i):
                dfi.delete()

    def cleanup_interfaces(self, interfaces):
        """
        Delete hanging interfaces
        :param interfaces: generator yielding interfaces names
        :return:
        """
        db_iface = set(
            i["name"] for i in Interface.objects.filter(managed_object=self.object.id).only("name")
        )
        for i in db_iface - set(interfaces):
            self.logger.info("Removing interface %s", i)
            di = Interface.objects.filter(managed_object=self.object.id, name=i).first()
            if di:
                di.delete()

    def cleanup_subinterfaces(self, forwarding_instance, interface, subinterfaces):
        """
        Delete hanging subinterfaces
        :return:
        """
        if forwarding_instance:
            fi = forwarding_instance.id
        else:
            fi = None
        qs = SubInterface.objects.filter(
            managed_object=self.object.id, interface=interface.id, forwarding_instance=fi
        )
        db_siface = set(i["name"] for i in qs.only("name"))
        for i in db_siface - set(subinterfaces):
            self.logger.info("Removing subinterface %s" % i)
            dsi = SubInterface.objects.filter(
                managed_object=self.object.id, interface=interface.id, name=i
            ).first()
            if dsi:
                dsi.delete()

    def interface_classification(self, iface):
        """
        Perform interface classification
        :param iface: Interface instance
        :return:
        """
        if iface.profile_locked:
            return
        try:
            p_id = self.get_interface_profile(iface)
        except NotImplementedError:
            self.logger.error("Uses not implemented rule")
            return
        if p_id and p_id != iface.profile.id:
            # Change profile
            profile = InterfaceProfile.get_by_id(p_id)
            if not profile:
                self.logger.error(
                    "Invalid interface profile '%s' for interface '%s'. " "Skipping",
                    p_id,
                    iface.name,
                )
                return
            elif profile != iface.profile:
                self.logger.info(
                    "Interface %s has been classified as '%s'", iface.name, profile.name
                )
                iface.profile = profile
                iface.save()

    def resolve_properties(self):
        """
        Try to resolve missed ifindexes and mac
        """
        ifindex, mac = True, False
        iface_discovery_policy = self.object.get_interface_discovery_policy()
        if iface_discovery_policy == "c":
            self.logger.info("Cannot resolve ifindexes due to policy")
            return
        elif iface_discovery_policy in {"C", "S"}:
            self.logger.info("Resolve ifindexes and macs by script")
            mac = True
        # Missed properties
        missed_properties = [
            n[1]
            for n in self.if_name_cache
            if (
                    n in self.if_name_cache
                    and self.if_name_cache[n]
                    and ((ifindex and self.if_name_cache[n].ifindex is None)
                         or (mac and self.if_name_cache[n].mac is None))
                    and self.if_name_cache[n].type in ("physical", "aggregated")
            )
        ]
        if not missed_properties:
            return
        self.logger.info("Missed properties for: %s", ", ".join(missed_properties))
        try:
            r = self.object.scripts.get_interface_properties(
                enable_ifindex=ifindex, enable_interface_mac=mac
            )
        except RPCError:
            r = None
        if not r:
            return
        updates = defaultdict(dict)
        for i in r:
            if i["interface"] not in missed_properties:
                continue
            if ifindex:
                updates[i["interface"]]["ifindex"] = i["ifindex"]
            if mac:
                updates[i["interface"]]["mac"] = i["mac"]
        if not updates:
            return
        for n, i in updates.items():
            iface = self.get_interface_by_name(n)
            if iface:
                if "ifindex" in i:
                    self.logger.info("Set ifindex for %s: %s", n, i["ifindex"])
                    iface.ifindex = i["ifindex"]
                if "mac" in i:
                    self.logger.info("Set mac for %s: %s", n, i["mac"])
                    iface.mac = i["mac"]
                iface.save()  # Signals will be sent

    @staticmethod
    def in_lag(x):
        return "aggregated_interface" in x and bool(x["aggregated_interface"])

    def get_policy(self):
        return self.object.get_interface_discovery_policy()

    def get_data_from_script(self):
        return self.object.scripts.get_interfaces()

    def get_data_from_confdb(self):
        # Get interfaces and parse result
        interfaces = {d["if_name"]: d for d in self.confdb.query(self.IF_QUERY)}
        vrfs = {(d["vr"], d["instance"]): d for d in self.confdb.query(self.VRF_QUERY)}
        iface_proto = {d["if_name"]: d for d in self.confdb.query(self.PROTOCOLS_QUERY)}
        instances = defaultdict(dict)
        for d in self.confdb.query(self.UNIT_QUERY):
            r = instances[d["vr"], d["instance"]]
            if not r:
                r["virtual_router"] = d["vr"]
                r["forwarding_instance"] = d["instance"]
                if vrfs and (d["vr"], d["instance"]) in vrfs:
                    try:
                        vrf = vrfs[d["vr"], d["instance"]]
                        r["type"] = vrf["type"]
                        if vrf.get("rd"):
                            r["rd"] = vrf["rd"]
                        r["rt_export"] = vrf.get("rt_export", [])
                        if vrf.get("rt_import"):
                            r["rt_import"] = vrf["rt_import"]
                        if "vpn_id" in vrf:
                            r["vpn_id"] = vrf["vpn_id"]
                        else:
                            r["vpn_id"] = get_vpn_id(
                                {
                                    "name": vrf["instance"],
                                    "rd": vrf.get("rd"),
                                    "rt_export": vrf.get("rt_export", []),
                                    "type": vrf["type"].upper()
                                    if vrf["type"] in ["vrf", "vpls", "vll"]
                                    else vrf["type"],
                                }
                            )
                    except ValueError:
                        pass
            if "interfaces" not in r:
                r["interfaces"] = {}
            if_name = d["if_name"]
            p_iface = interfaces.get(if_name)
            iface = r["interfaces"].get(if_name)
            if iface is None:
                iface = {
                    "name": if_name,
                    "type": p_iface.get("type", "unknown") if p_iface else "unknown",
                    "admin_status": False,
                    "enabled_protocols": [],
                    "subinterfaces": {},
                }
                r["interfaces"][if_name] = iface
                if p_iface:
                    if "description" in p_iface:
                        iface["description"] = p_iface["description"]
                    if "admin_status" in p_iface:
                        iface["admin_status"] = p_iface["admin_status"] == "on"
                    if if_name in iface_proto:
                        if iface_proto[if_name]["stp_status"] == "on":
                            iface["enabled_protocols"] += ["STP"]
                        if iface_proto[if_name]["lldp_status"] == "tx":
                            iface["enabled_protocols"] += ["LLDP"]
            unit = iface["subinterfaces"].get(d["unit"])
            if unit is None:
                unit = {"name": d["unit"], "enabled_afi": []}
                iface["subinterfaces"][d["unit"]] = unit
            unit = iface["subinterfaces"][d["unit"]]
            description = d.get("description")
            if description:
                unit["description"] = description
            elif p_iface and p_iface.get("description"):
                unit["description"] = p_iface["description"]
            if "ipv4_addresses" in d:
                unit["enabled_afi"] += ["IPv4"]
                unit["ipv4_addresses"] = d["ipv4_addresses"]
            if "ipv6_addresses" in d:
                unit["enabled_afi"] += ["IPv6"]
                unit["ipv6_addresses"] = d["ipv4_addresses"]
            if "tagged" in d or "untagged" in d:
                unit["enabled_afi"] += ["BRIDGE"]
            if "untagged" in d:
                unit["untagged_vlan"] = int(d["untagged"])
            if "tagged" in d:
                unit["tagged_vlans"] = ranges_to_list(d["tagged"])
        # Flatten units
        r = list(instances.values())
        for fi in r:
            # Flatten interfaces
            fi["interfaces"] = list(fi["interfaces"].values())
            # Flatten units
            for i in fi["interfaces"]:
                i["subinterfaces"] = list(i["subinterfaces"].values())
        return IGetInterfaces().clean_result(r)

    def collate(self, if_map: Dict[str, Interface]) -> None:
        """
        Collation is the process of binding between physical and logical inventory.
        I.e. assigning interface names to inventory slots.

        :param if_map:
        :returns:
        """

        def path_to_str(p):
            return " > ".join(x.connection.name for x in p)

        if not self.object.object_profile.enable_box_discovery_asset:
            self.logger.info("asset discovery is disabled. Skipping collation process")
            return
        if not if_map:
            self.logger.info("No interfaces found. Skipping collation process")
            return
        # Build collators chain
        chain = list(self.object.profile.get_profile().iter_collators(self.object))
        if not chain:
            self.logger.info("Collator chain is empty. Skipping collation process.")
            return
        # Perform collation
        self.logger.info("Starting interface collation")
        mappings = defaultdict(list)  # object -> [(connection_name, if_name), ...]
        seen_objects = set()  # {object}
        obj_combined = {}  # object -> connection name -> parent name
        obj_ifnames = {}  # object -> connection name -> interface name
        for path in self.object.iter_scope("physical"):
            if_name = None
            obj = path[-1].object
            if obj not in seen_objects:
                obj_combined[obj] = {c.name: c.combo for c in obj.model.connections if c.combo}
                obj_ifnames[obj] = {}
                seen_objects.add(obj)
            cn = path[-1].connection.name
            parent = obj_combined[obj].get(cn)
            if parent:
                # Combined port, try to resolve against parent
                if_name = obj_ifnames[obj].get(parent)
                if if_name:
                    # Parent is already bound
                    obj_ifnames[obj][cn] = if_name
                    mappings[obj] += [(path, if_name)]
                    self.logger.info(
                        "%s mapped to interface %s via parent %s",
                        path_to_str(path),
                        if_name,
                        parent,
                    )
            if not if_name:
                for collator in chain:
                    if_name = collator.collate(path, if_map)
                    if if_name:
                        obj_ifnames[obj][cn] = if_name
                        mappings[obj] += [(path, if_name)]
                        self.logger.info("%s mapped to interface %s", path_to_str(path), if_name)
                        break
            if not if_name:
                self.logger.info("Unable to map %s to interface", path_to_str(path))
        # Bulk update data
        for obj in seen_objects:
            old_if_map = {c.name: c.interface_name for c in obj.connections if c.interface_name}
            changed = False
            for path, if_name in mappings[obj]:
                connection_name = path[-1].connection.name
                if connection_name not in old_if_map:
                    # New
                    self.logger.info("Map %s to %s", path_to_str(path), if_name)
                    obj.set_connection_interface(connection_name, if_name)
                    changed = True
                    continue
                if old_if_map[connection_name] != if_name:
                    # Changed
                    self.logger.info(
                        "Map %s to %s (was %s)",
                        path_to_str(path),
                        if_name,
                        old_if_map[connection_name],
                    )
                    obj.set_connection_interface(connection_name, if_name)
                    changed = True
                # Mark as processed
                del old_if_map[connection_name]
            if old_if_map:
                # Process removed
                for connection_name in old_if_map:
                    self.logger.info(
                        "Unmap %s from %s", connection_name, old_if_map[connection_name]
                    )
                    obj.reset_connection_interface(connection_name)
                changed = True
            # Apply changes
            if changed:
                obj.save()
