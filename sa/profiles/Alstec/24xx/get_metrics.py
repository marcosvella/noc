# ---------------------------------------------------------------------
# Alstec.24xx.get_metrics
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import Script as GetMetricsScript, metrics
from noc.core.text import parse_table


class Script(GetMetricsScript):
    name = "Alstec.24xx.get_metrics"

    @metrics(["CPU | Load | 1min"], volatile=False, access="C")  # CLI version
    def get_cpu_metrics(self, metrics):
        v = self.cli("show process cpu")
        v = parse_table(v)
        if v:
            self.set_metric(id=("CPU | Load | 1min", None), value=float(v[-1][-1][:-1]))

    @metrics(["Memory | Load | 1min"], volatile=False, access="C")  # CLI version
    def get_memory_metrics(self, metrics):
        v = self.cli("show resources")
        r = {}
        column = None
        for line in v.splitlines():
            if not line:
                continue
            if not line.startswith("  "):
                column = line.strip().lower()
            if column:
                k, v = line.split(":")
                r[column + k.strip().lower()] = v.strip()
        if r.get("ram:total") and r.get("ram:used"):
            used = int(r.get("ram:used").split(" ")[0])
            total = int(r.get("ram:total").split(" ")[0])
            self.set_metric(id=("Memory | Load | 1min", None), value=round(used * 100.0 / total))

    @metrics(
        ["Interface | Errors | CRC", "Interface | Errors | Frame"],
        has_capability="DB | Interfaces",
        volatile=False,
        matcher="is_builtin_controller",
        access="C",  # CLI version
    )
    def get_interface_metrics(self, metrics):
        v = self.cli("show box-shso counters")
        v = self.profile.parse_kv_out(v)
        metric_map = {
            "CRC errors": "Interface | Errors | CRC",
            "Invalid frame length": "Interface | Errors | Frame",
        }
        for iface in v:
            for m in metric_map:
                if m not in v[iface]:
                    continue
                self.set_metric(id=(metric_map[m], ["noc::port::0/0"]), value=int(v[iface][m]))

    @metrics(
        [
            "Environment | Electric current",
            "Environment | Sensor Status",
            "Environment | Temperature",
            "Environment | Voltage",
        ],
        volatile=False,
        matcher="is_builtin_controller",
        access="C",  # CLI version
    )
    def get_boxshso_metrics(self, metrics):
        modules = {
            "black_box": "show box-shso bb",
            "battery_pack": "show box-shso bp",
            "main_power_supply": "show box-shso pum",
        }
        for module, command in modules.items():
            try:
                v = self.cli(command)
            except self.CLISyntaxError:
                continue
            v = self.profile.parse_kv_out(v)
            for m, v in v.items():
                m = m.lower()
                if m.startswith("temperature"):
                    self.set_metric(
                        id=("Environment | Temperature", None),
                        metric="Environment | Temperature",
                        labels=["noc::name::Temperature_%s" % module],
                        value=float(v.split()[0]),
                        multi=True,
                    )
                elif "voltage" in m:
                    self.set_metric(
                        id=("Environment | Voltage", None),
                        metric="Environment | Voltage",
                        labels=["noc::name::Voltage_%s" % module],
                        value=float(v.split()[0]),
                        multi=True,
                    )
                elif "current" in m:
                    self.set_metric(
                        id=("Environment | Electric current", None),
                        metric="Environment | Electric current",
                        labels=["noc::name::ElectricCurrent_%s" % module],
                        value=float(v.split()[0]) * 1000.0,
                        multi=True,
                    )
                elif "door state" in m:
                    self.set_metric(
                        id=("Environment | Sensor Status", None),
                        metric="Environment | Sensor Status",
                        labels=["noc::name::State_Door"],
                        value=bool("Open" in v),
                        multi=True,
                    )
                elif "batteries circuit-breaker state" in m:
                    self.set_metric(
                        id=("Environment | Sensor Status", None),
                        metric="Environment | Sensor Status",
                        labels=["noc::name::State_Batteries"],
                        value=bool("On" in v),
                        multi=True,
                    )
