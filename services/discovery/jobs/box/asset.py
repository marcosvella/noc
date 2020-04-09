# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Asset check
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
from collections import defaultdict
import hashlib
import base64
from threading import Lock
import operator
import re

# Third-party modules
import cachetools

# NOC modules
from noc.services.discovery.jobs.base import DiscoveryCheck
from noc.inv.models.objectmodel import ObjectModel
from noc.inv.models.object import Object
from noc.inv.models.vendor import Vendor
from noc.inv.models.unknownmodel import UnknownModel
from noc.inv.models.modelmapping import ModelMapping
from noc.inv.models.error import ConnectionError
from noc.core.text import str_dict
from noc.core.comp import smart_bytes


class AssetCheck(DiscoveryCheck):
    """
    Version discovery
    """

    name = "asset"
    required_script = "get_inventory"

    _serial_masks = {}
    _serial_masks_lock = Lock()

    def __init__(self, *args, **kwargs):
        super(AssetCheck, self).__init__(*args, **kwargs)
        self.unknown_part_no = {}  # part_no -> list of variants
        self.pn_description = {}  # part_no -> Description
        self.vendors = {}  # code -> Vendor instance
        self.objects = []  # [(type, object, context, serial)]
        self.to_disconnect = (
            set()
        )  # Save processed connection. [(in_connection, object, out_connection), ... ]
        self.rule = defaultdict(list)  # Connection rule. type -> [rule1, ruleN]
        self.rule_context = {}
        self.ctx = {}
        self.stack_member = {}  # object -> stack member numbers
        self.managed = set()  # Object ids
        self.unk_model = {}  # name -> model
        self.lost_and_found = self.get_lost_and_found(self.object)

    def handler(self):
        self.logger.info("Checking assets")
        result = self.object.scripts.get_inventory()
        self.find_managed()
        # Submit objects
        for o in result:
            self.logger.info("Submit %s", str_dict(o))
            self.submit(
                type=o["type"],
                number=o.get("number"),
                builtin=o["builtin"],
                vendor=o.get("vendor"),
                part_no=o["part_no"],
                revision=o.get("revision"),
                serial=o.get("serial"),
                mfg_date=o.get("mfg_date"),
                description=o.get("description"),
            )
        # Assign stack members
        self.submit_stack_members()
        #
        self.submit_connections()
        #
        self.check_management()
        #
        self.disconnect_connections()

    def submit(
        self,
        type,
        part_no,
        number=None,
        builtin=False,
        vendor=None,
        revision=None,
        serial=None,
        mfg_date=None,
        description=None,
    ):
        # Check the vendor and the serial are sane
        # OEM transceivers return binary trash often
        if vendor:
            # Possible dead code
            try:
                vendor.encode("utf-8")
            except UnicodeDecodeError:
                self.logger.info("Trash submited as vendor id: %s", vendor.encode("hex"))
                return
        if serial:
            # Possible dead code
            try:
                serial.encode("utf-8")
            except UnicodeDecodeError:
                self.logger.info("Trash submited as serial: %s", serial.encode("hex"))
                return
        #
        is_unknown_xcvr = not builtin and part_no[0].startswith("Unknown | Transceiver | ")
        if not type and is_unknown_xcvr:
            type = "XCVR"
        # Skip builtin modules
        if builtin:
            # Adjust context anyway
            self.prepare_context(type, number)
            return  # Builtin must aways have type set
        #
        if is_unknown_xcvr:
            self.logger.info("%s S/N %s should be resolved later", part_no[0], serial)
            self.prepare_context(type, number)
            self.objects += [("XCVR", part_no[0], self.ctx.copy(), serial)]
            return
        # Cache description
        if description:
            for p in part_no:
                if p not in self.pn_description:
                    self.pn_description[p] = description
        # Find vendor
        vnd = self.get_vendor(vendor)
        if not vnd:
            # Try to resolve via model map
            m = self.get_model_map(vendor, part_no, serial)
            if not m:
                self.logger.error(
                    "Unknown vendor '%s' for S/N %s (%s)", vendor, serial, description
                )
                return
        else:
            # Find model
            m = ObjectModel.get_model(vnd, part_no)
            if not m:
                # Try to resolve via model map
                m = self.get_model_map(vendor, part_no, serial)
                if not m:
                    self.logger.info(
                        "Unknown model: vendor=%s, part_no=%s (%s). " "Skipping",
                        vnd.name,
                        part_no,
                        description,
                    )
                    self.register_unknown_part_no(vnd, part_no, description)
                    return
        # Sanitize serial number against the model
        serial = self.clean_serial(m, number, serial)
        #
        if m.cr_context and type != m.cr_context:
            # Override type with object mode's one
            self.logger.info("Model changes type to '%s'", m.cr_context)
            type = m.cr_context
        if not type:
            self.logger.info(
                "Cannot resolve type for: vendor=%s, part_no=%s (%s). " "Skipping",
                vnd.name,
                description,
                part_no,
            )
            return
        self.prepare_context(type, number)
        # Get connection rule
        if not self.rule and m.connection_rule:
            self.set_rule(m.connection_rule)
            # Set initial context
            if type in self.rule_context:
                scope = self.rule_context[type][0]
                if scope:
                    self.set_context(scope, number)
        # Find existing object or create new
        o = Object.objects.filter(model=m.id, data__asset__serial=serial).first()
        if not o:
            # Create new object
            self.logger.info("Creating new object. model='%s', serial='%s'", m.name, serial)
            data = {"asset": {"serial": serial}}
            if revision:
                data["asset"]["revision"] = revision
            if mfg_date:
                data["asset"]["mfg_date"] = mfg_date
            if self.object.container:
                container = self.object.container.id
            else:
                container = self.lost_and_found
            o = Object(model=m, data=data, container=container)
            o.save()
            o.log(
                "Created by asset_discovery",
                system="DISCOVERY",
                managed_object=self.object,
                op="CREATE",
            )
        else:
            # Add all connection to disconnect list
            self.to_disconnect.update(
                set((o, c[0], c[1], c[2]) for c in o.iter_inner_connections())
            )
        # Check revision
        if o.get_data("asset", "revision") != revision:
            # Update revision
            self.logger.info(
                "Object revision changed [%s %s] %s -> %s",
                m.name,
                o.id,
                o.get_data("asset", "revision"),
                revision,
            )
            o.set_data("asset", "revision", revision)
            o.save()
            o.log(
                "Object revision changed: %s -> %s" % (o.get_data("asset", "revision"), revision),
                system="DISCOVERY",
                managed_object=self.object,
                op="CHANGE",
            )
        # Check manufacturing date
        if mfg_date and o.get_data("asset", "revision") != revision:
            # Update revision
            self.logger.info(
                "Object manufacturing date changed [%s %s] %s -> %s",
                m.name,
                o.id,
                o.get_data("asset", "mfg_date"),
                mfg_date,
            )
            o.set_data("asset", "mfg_date", mfg_date)
            o.save()
            o.log(
                "Object manufacturing date: %s -> %s" % (o.get_data("asset", "mfg_date"), mfg_date),
                system="DISCOVERY",
                managed_object=self.object,
                op="CHANGE",
            )
        # Check management
        if o.get_data("management", "managed"):
            if o.get_data("management", "managed_object") != self.object.id:
                self.logger.info("Changing object management to '%s'", self.object.name)
                o.set_data("management", "managed_object", self.object.id)
                o.save()
                o.log(
                    "Management granted",
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="CHANGE",
                )
            self.update_name(o)
            if o.id in self.managed:
                self.managed.remove(o.id)
        self.objects += [(type, o, self.ctx.copy(), serial)]
        # Collect stack members
        if number and o.get_data("stack", "stackable"):
            self.stack_member[o] = number

    def prepare_context(self, type, number):
        self.set_context("N", number)
        if type and type in self.rule_context:
            scope, reset_scopes = self.rule_context[type]
            if scope:
                self.set_context(scope, number)
            if reset_scopes:
                self.reset_context(reset_scopes)

    def update_name(self, object):
        n = self.get_name(object, self.object)
        if n and n != object.name:
            object.name = n
            self.logger.info("Changing name to '%s'", n)
            object.save()
            object.log(
                "Change name to '%s'" % n,
                system="DISCOVERY",
                managed_object=self.object,
                op="CHANGE",
            )

    def iter_object(self, i, scope, value, target_type, fwd):
        # Search backwards
        if not fwd:
            for j in range(i - 1, -1, -1):
                type, object, ctx, _ = self.objects[j]
                if scope in ctx and ctx[scope] == value:
                    if target_type == type:
                        yield type, object, ctx
                else:
                    break
        # Search forward
        if fwd:
            for j in range(i + 1, len(self.objects)):
                type, object, ctx, _ = self.objects[j]
                if scope in ctx and ctx[scope] == value:
                    if target_type == type:
                        yield type, object, ctx
                else:
                    raise StopIteration

    def expand_context(self, s, ctx):
        """
        Replace values in context
        """
        s = s or ""
        for c in ctx:
            s = s.replace("{%s}" % c, str(ctx[c]))
        return s

    def submit_connections(self):
        # Check connection rule is set
        if not self.rule:
            return
        for i, o in enumerate(self.objects):
            type, object, context, serial = o
            self.logger.info("Trying to connect #%d. %s (%s)", i, type, str_dict(context))
            if type not in self.rule:
                continue
            # Find applicable rule
            for r in self.rule[type]:
                found = False
                t_n = self.expand_context(r.target_number, context)
                if r.scope.startswith("-"):
                    scope = r.scope[1:]
                    fwd = True
                else:
                    scope = r.scope
                    fwd = False
                for t_type, t_object, t_ctx in self.iter_object(
                    i, scope, context.get(scope), r.target_type, fwd=fwd
                ):
                    if isinstance(t_object, str):
                        continue
                    if not t_n or t_n == t_ctx["N"]:
                        # Check target object has proper connection
                        t_c = self.expand_context(r.target_connection, context)
                        if not t_object.has_connection(t_c):
                            continue
                        # Check source object has proper connection
                        m_c = self.expand_context(r.match_connection, context)
                        if isinstance(object, str):
                            # Resolving unknown object
                            o = self.resolve_object(object, m_c, t_object, t_c, serial)
                            if not o:
                                continue
                            object = o
                        if not object.has_connection(m_c):
                            continue
                        # Connect
                        self.logger.info(
                            "Connecting %s %s:%s -> %s %s:%s",
                            type,
                            context["N"],
                            m_c,
                            t_type,
                            t_ctx["N"],
                            t_c,
                        )
                        if object.get_data("twinax", "twinax") and m_c == object.get_data(
                            "twinax", "alias"
                        ):
                            self.connect_twinax(object, m_c, t_object, t_c)
                        else:
                            self.connect_p2p(object, m_c, t_object, t_c)
                        found = True
                        break
                if found:
                    break

    def connect_p2p(self, o1, c1, o2, c2):
        """
        Create P2P connection o1:c1 - o2:c2
        """
        try:
            cn = o1.connect_p2p(c1, o2, c2, {}, reconnect=True)
            if cn:
                o1.log(
                    "Connect %s -> %s:%s" % (c1, o2, c2),
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="CONNECT",
                )
                o2.log(
                    "Connect %s -> %s:%s" % (c2, o1, c1),
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="CONNECT",
                )
            c_name = o2.model.get_model_connection(c2)  # If internal_name use
            if (o2, c_name.name, o1, c1) in self.to_disconnect:
                # Remove if connection on system
                self.to_disconnect.remove((o2, c_name.name, o1, c1))
        except ConnectionError as e:
            self.logger.error("Failed to connect: %s", e)

    def connect_twinax(self, o1, c1, o2, c2):
        """
        Connect twinax object o1 and virtual connection c1 to o2:c2
        """
        free_connections = []
        # Resolve virtual name c1 to real connection
        r_names = [o1.get_data("twinax", "connection%d" % i) for i in range(1, 3)]
        # Check connection is already exists
        for n in r_names:
            cn, o, c = o1.get_p2p_connection(n)
            if not cn:
                free_connections += [n]
                continue
            if o.id == o2.id and c == c2:
                # Already connected
                return
        # Check twinax has free connection
        if not free_connections:
            self.logger.error("Twinax has no free connections")
            return
        # Connect first free to o2:c2
        c = free_connections[0]
        self.logger.info("Using twinax connection '%s' instead of '%s'", c, c1)
        self.connect_p2p(o1, c, o2, c2)

    def submit_stack_members(self):
        if len(self.stack_member) < 2:
            return
        for o in self.stack_member:
            m = self.stack_member[o]
            if o.get_data("stack", "member") != m:
                self.logger.info("Setting stack member %s", m)
                o.set_data("stack", "member", m)
                o.save()
                o.log(
                    "Setting stack member %s" % m,
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="CHANGE",
                )
                self.update_name(o)

    def send(self):
        if self.unknown_part_no:
            platform = self.object.platform
            upn = self.get_unknown_part_no()
            for pns in upn:
                # Find description
                description = "no description"
                for p in pns:
                    if p in self.pn_description:
                        description = self.pn_description[p]
                        break
                # Report error
                self.logger.error(
                    "Unknown part number for %s: %s (%s)", platform, ", ".join(pns), description
                )

    def register_unknown_part_no(self, vendor, part_no, descripton):
        """
        Register missed part number
        """
        if not isinstance(part_no, list):
            part_no = [part_no]
        for p in part_no:
            if p not in self.unknown_part_no:
                self.unknown_part_no[p] = set()
            for pp in part_no:
                self.unknown_part_no[p].add(pp)
            UnknownModel.mark_unknown(vendor.code[0], self.object, p, descripton)

    def get_unknown_part_no(self):
        """
        Get list of missed part number variants
        """
        r = []
        for p in self.unknown_part_no:
            n = sorted(self.unknown_part_no[p])
            if n not in r:
                r += [n]
        return r

    def get_vendor(self, v):
        """
        Get vendor instance or None
        """
        if v is None or v.startswith("OEM") or v == "None":
            v = "NONAME"
        v = v.upper()
        if v in self.vendors:
            return self.vendors[v]
        # Temporary fix
        if v == "D-LINK":
            v = "DLINK"
        if "INTEL" in v:
            v = "INTEL"
        if "FINISAR" in v:
            v = "FINISAR"
        o = Vendor.objects.filter(code=v).first()
        if o:
            self.vendors[v] = o
            return o
        else:
            self.vendors[v] = None
            return None

    def set_rule(self, rule):
        self.logger.debug("Setting connection rule '%s'", rule.name)
        # Compile context mappings
        self.rule_context = {}
        for ctx in rule.context:
            self.rule_context[ctx.type] = (ctx.scope, ctx.reset_scopes)
        self.logger.debug("Context mappings: %s", self.rule_context)
        # Compile rules
        for r in rule.rules:
            self.rule[r.match_type] += [r]

    def set_context(self, name, value):
        self.ctx[name] = value
        n = "N%s" % name
        if n not in self.ctx:
            self.ctx[n] = 0
        else:
            self.ctx[n] += 1
        self.logger.debug("Set context %s = %s -> %s", name, value, str_dict(self.ctx))

    def reset_context(self, names):
        for n in names:
            if n in self.ctx:
                del self.ctx[n]
            m = "N%s" % n
            if m in self.ctx:
                del self.ctx[m]
        self.logger.debug("Reset context scopes %s -> %s", ", ".join(names), str_dict(self.ctx))

    def find_managed(self):
        """
        Get all objects managed by managed object
        """
        self.managed = set(
            Object.objects.filter(data__management__managed_object=self.object.id).values_list("id")
        )

    def check_management(self):
        """
        Unmanage all left objects
        """
        for oid in self.managed:
            o = Object.objects.filter(id=oid).first()
            if o:
                self.logger.info("Revoking management from %s %s", o.model.name, o.id)
                o.reset_data("management", "managed_object")
                o.save()
                o.log(
                    "Management revoked",
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="CHANGE",
                )

    def resolve_object(self, name, m_c, t_object, t_c, serial):
        """
        Resolve object type
        """
        # Check object is already exists
        c, object, c_name = t_object.get_p2p_connection(t_c)
        if c is not None:
            if c_name == m_c and object.get_data("asset", "serial") == serial:
                # Object with same serial number exists
                return object
            else:
                # Serial number/connection mismatch
                return None
        # Check connection type
        c = t_object.model.get_model_connection(t_c)
        if c is None:
            self.logger.error("Connection violation for %s SN %s", name, serial)
            return None  # ERROR
        # Transceiver formfactor
        tp = c.type.name.split(" | ")
        ff = tp[1]
        m = "NoName | Transceiver | Unknown %s" % ff
        if name != "Unknown | Transceiver | Unknown":
            mtype = name[24:].upper().replace("-", "")
            if "BASE" in mtype:
                speed, ot = mtype.split("BASE", 1)
                spd = {"100": "100M", "1000": "1G", "10G": "10G"}.get(speed)
                if spd:
                    m = "NoName | Transceiver | %s | %s %s" % (spd, ff, ot)
                else:
                    self.logger.error("Unknown transceiver speed: %s", speed)
                    m = name
            else:
                m = name
        # Add vendor suffix when necessary
        if len(tp) == 3:
            m += " | %s" % tp[2]
        #
        if m in self.unk_model:
            model = self.unk_model[m]
        else:
            model = ObjectModel.objects.filter(name=m).first()
            self.unk_model[m] = model
        if not model:
            self.logger.error("Unknown model '%s'", m)
            self.register_unknown_part_no(self.get_vendor("NONAME"), m, "%s -> %s" % (name, m))
            return None
        # Create object
        self.logger.info("Creating new object. model='%s', serial='%s'", m, serial)
        if self.object.container:
            container = self.object.container.id
        else:
            container = self.lost_and_found
        o = Object(model=model, data={"asset": {"serial": serial}}, container=container)
        o.save()
        o.log(
            "Created by asset_discovery",
            system="DISCOVERY",
            managed_object=self.object,
            op="CREATE",
        )
        return o

    def get_model_map(self, vendor, part_no, serial):
        """
        Try to resolve using model map
        """
        # Process list of part no
        if isinstance(part_no, list):
            for p in part_no:
                m = self.get_model_map(vendor, p, serial)
                if m:
                    return m
            return None
        for mm in ModelMapping.objects.filter(vendor=vendor, is_active=True):
            if mm.part_no and mm.part_no != part_no:
                continue
            if mm.from_serial and mm.to_serial:
                if mm.from_serial <= serial and serial <= mm.to_serial:
                    return True
            else:
                self.logger.debug("Mapping %s %s %s to %s", vendor, part_no, serial, mm.model.name)
                return mm.model
        return None

    def get_lost_and_found(self, object):
        lfm = ObjectModel.objects.filter(name="Lost&Found").first()
        if not lfm:
            self.logger.error("Lost&Found model not found")
            return None
        lf = Object.objects.filter(model=lfm.id).first()
        if not lf:
            self.logger.error("Lost&Found not found")
            return None
        return lf.id

    def generate_serial(self, model, number):
        """
        Generate virtual serial number
        """
        seed = [str(self.object.id), str(model.uuid), str(number)]
        for k in sorted(x for x in self.ctx if not x.startswith("N")):
            seed += [k, str(self.ctx[k])]
        h = hashlib.sha256(smart_bytes(":".join(seed)))
        return "NOC%s" % base64.b32encode(h.digest())[:7]

    @staticmethod
    def get_name(obj, managed_object=None):
        """
        Generate discovered object's name
        """
        name = None
        if managed_object:
            name = managed_object.name
            sm = obj.get_data("stack", "member")
            if sm is not None:
                # Stack member
                name += "#%s" % sm
        return name

    def disconnect_connections(self):
        for o1, c1, o2, c2 in self.to_disconnect:
            self.logger.info("Disconnect: %s:%s ->X<- %s:%s", o1, c1, c2, o2)
            self.disconnect_p2p(o1, c1, c2, o2)

    def disconnect_p2p(self, o1, c1, c2, o2):
        """
        Disconnect P2P connection o1:c1 - o2:c2
        """
        try:
            cn = o1.get_p2p_connection(c1)[0]
            if cn:
                o1.log(
                    "Disconnect %s -> %s:%s" % (c1, o2, c2),
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="DISCONNECT",
                )
                o2.log(
                    "Disconnect %s -> %s:%s" % (c2, o1, c1),
                    system="DISCOVERY",
                    managed_object=self.object,
                    op="DISCONNECT",
                )
                cn.delete()
        except ConnectionError as e:
            self.logger.error("Failed to disconnect: %s", e)

    def clean_serial(self, model, number, serial):
        # Empty value
        if not serial or serial == "None":
            new_serial = self.generate_serial(model, number)
            self.logger.info("Empty serial number. Generating virtual serial %s", new_serial)
            return new_serial
        # Too short value
        slen = len(serial)
        min_serial_size = model.get_data("asset", "min_serial_size")
        if min_serial_size is not None and slen < min_serial_size:
            new_serial = self.generate_serial(model, number)
            self.logger.info(
                "Invalid serial number '%s': Too short, must be %d symbols or more. "
                "Replacing with virtual serial %s",
                serial,
                min_serial_size,
                new_serial,
            )
            return new_serial
        # Too long value
        max_serial_size = model.get_data("asset", "max_serial_size")
        if max_serial_size is not None and slen > max_serial_size:
            new_serial = self.generate_serial(model, number)
            self.logger.info(
                "Invalid serial number '%s': Too long, must be %d symbols or less. "
                "Replacing with virtual serial %s",
                serial,
                max_serial_size,
                new_serial,
            )
            return new_serial
        # Regular expression
        serial_mask = model.get_data("asset", "serial_mask")
        if serial_mask:
            rx = self.get_serial_mask(serial_mask)
            if not rx.match(serial):
                new_serial = self.generate_serial(model, number)
                self.logger.info(
                    "Invalid serial number '%s': Must match mask '%s'. "
                    "Replacing with virtual serial %s",
                    serial,
                    serial_mask,
                    new_serial,
                )
                return new_serial
        return serial

    @cachetools.cachedmethod(
        operator.attrgetter("_serial_masks"), lock=operator.attrgetter("_serial_masks_lock")
    )
    def get_serial_mask(self, mask):
        """
        Compile serial mask and cache value
        :param mask:
        :return:
        """
        return re.compile(mask)
