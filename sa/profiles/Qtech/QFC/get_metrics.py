# ---------------------------------------------------------------------
# Qtech.QFC.get_metrics
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import Script as GetMetricsScript, metrics
from core.script.metrics import scale
from noc.core.validators import is_float, is_int


class Script(GetMetricsScript):
    name = "Qtech.QFC.get_metrics"

    def check_oid(self):
        if self.is_lite:
            return 103
        return 102

    @metrics(["Environment | Sensor Status"], volatile=False, access="S")  # SNMP version
    def get_sensor_status(self, metrics):
        for metric in metrics:
            if metric.ifindex == 100:
                continue
            value = 1
            if self.is_lite:
                status = self.snmp.get("1.3.6.1.4.1.27514.103.0.%s.0" % metric.ifindex)
                if metric.ifindex in [5, 6, 7, 13] and status == 1:
                    value = 0
                elif metric.ifindex in [8, 9] and -55 < status < 600:
                    value = 0
                elif metric.ifindex in [27] and status > 0:
                    value = 0
            else:
                status = self.snmp.get("1.3.6.1.4.1.27514.102.0.%s.0" % metric.ifindex)
                if metric.ifindex in [5, 6, 13] and status == 1:
                    value = 0
                elif metric.ifindex in [8] and status > 0:
                    value = 0
                elif metric.ifindex in [9, 10] and -55 < status < 600:
                    value = 0
                elif metric.ifindex in [16] and status > 0:
                    value = 0
            self.set_metric(
                id=("Environment | Sensor Status", metric.path),
                value=value,
            )

    @metrics(["Environment | Temperature"], volatile=False, access="S")  # SNMP version
    def get_temperature(self, metrics):
        for metric in metrics:
            if "temp" in metric.path[3]:
                value = self.snmp.get(
                    "1.3.6.1.4.1.27514.%s.0.%s.0" % (self.check_oid(), metric.ifindex)
                )
                self.set_metric(
                    id=("Environment | Temperature", metric.path),
                    path=["", "", metric.path[3], metric.path[3]],
                    value=value,
                    multi=True,
                )
            if "ups" in metric.path[3]:
                if self.is_lite:
                    value = self.snmp.get("1.3.6.1.4.1.27514.103.0.26.0")
                    self.set_metric(
                        id=("Environment | Temperature", metric.path),
                        path=["", "", "battery", metric.path[3]],
                        value=value,
                        scale=scale(0.1, 2),
                        multi=True,
                    )

    @metrics(["Environment | Voltage"], volatile=False, access="S")  # SNMP version
    def get_voltage(self, metrics):
        for metric in metrics:
            if self.is_lite:
                value = self.snmp.get("1.3.6.1.4.1.27514.103.0.24.0")
                self.set_metric(
                    id=("Environment | Voltage", metric.path),
                    path=["", "", "battery", metric.path[3]],
                    value=value,
                    scale=scale(0.1, 2),
                    multi=True,
                )

    @metrics(["Environment | Electric Current"], volatile=False, access="S")  # SNMP version
    def get_current_input(self, metrics):
        for metric in metrics:
            if self.is_lite:
                value = self.snmp.get("1.3.6.1.4.1.27514.103.0.28.0")
            else:
                value = self.snmp.get("1.3.6.1.4.1.27514.102.0.17")
            if is_float(value) or is_int(value):
                self.set_metric(
                    id=("Environment | Electric Current", metric.path), value=value, scale=scale(10)
                )

    @metrics(["Environment | Energy Consumption"], volatile=False, access="S")  # SNMP version
    def get_energy_cons(self, metrics):
        for metric in metrics:
            if self.is_lite:
                value = self.snmp.get("1.3.6.1.4.1.27514.103.0.30.0")
            else:
                value = self.snmp.get("1.3.6.1.4.1.27514.102.0.19")
            self.set_metric(
                id=("Environment | Energy Consumption", metric.path),
                value=value,
                scale=scale(0.01, 2),
            )

    @metrics(["Environment | Power"], volatile=False, access="S")  # SNMP version
    def get_power(self, metrics):
        for metric in metrics:
            if self.is_lite:
                value = self.snmp.get("1.3.6.1.4.1.27514.103.0.29.0")
            else:
                value = self.snmp.get("1.3.6.1.4.1.27514.102.0.18")
            if value:
                self.set_metric(
                    id=("Environment | Power", metric.path),
                    value=value,
                )

    @metrics(["Environment | Power | Input | Status"], volatile=False, access="S")  # SNMP version
    def get_power_input_status(self, metrics):
        for metric in metrics:
            value = 1
            if self.is_lite:
                if "ups" in metric.path[3]:
                    value = self.snmp.get("1.3.6.1.4.1.27514.103.0.18.0")
                elif "220" in metric.path[3]:
                    res = self.snmp.get("1.3.6.1.4.1.27514.103.0.7.0")
                    if res == 1:
                        value = 0
            else:
                if "220" in metric.path[3]:
                    res = self.snmp.get("1.3.6.1.4.1.27514.102.0.8")
                    if res != 0:
                        value = 0
            self.set_metric(id=("Environment | Power | Input | Status", metric.path), value=value)

    @metrics(
        ["Environment | Battery | Capacity | Level"], volatile=False, access="S"
    )  # SNMP version
    def get_battery_capacity(self, metrics):
        for metric in metrics:
            if self.is_lite:
                value = self.snmp.get("1.3.6.1.4.1.27514.103.0.25.0")
                self.set_metric(
                    id=("Environment | Battery | Capacity | Level", metric.path),
                    value=value,
                )
