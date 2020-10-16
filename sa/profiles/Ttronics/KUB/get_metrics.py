# ---------------------------------------------------------------------
# Ttronics.KUB.get_metrics
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import Script as GetMetricsScript, metrics
from core.script.metrics import scale


class Script(GetMetricsScript):
    name = "Ttronics.KUB.get_metrics"

    @metrics(["Environment | Sensor Status"], volatile=False, access="S")  # SNMP version
    def get_interface_admin_status(self, metrics):
        for metric in metrics:
            if metric.ifindex == 100:
                continue
            value = 1
            status = self.snmp.get("1.3.6.1.4.1.51315.1.%s.0" % metric.ifindex)
            if metric.ifindex == 1:
                if status != -128:
                    value = 0
            elif metric.ifindex == 3 and status == 0:
                s_type = self.snmp.get("1.3.6.1.4.1.51315.1.15.0")
                if s_type == 0 and status == 0:
                    value = 0
            elif metric.ifindex == 4 and status == 0:
                s_type = self.snmp.get("1.3.6.1.4.1.51315.1.16.0")
                s_status = self.snmp.get("1.3.6.1.4.1.51315.1.2.0")
                if s_type == 4 and s_status == 0:
                    value = s_status
            else:
                value = status
            self.set_metric(
                id=("Environment | Sensor Status", metric.path),
                value=value,
            )

    @metrics(["Environment | Temperature"], volatile=False, access="S")  # SNMP version
    def get_temperature(self, metrics):
        for metric in metrics:
            if metric.ifindex == 1:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.%s.0" % metric.ifindex)
                self.set_metric(
                    id=("Environment | Temperature", metric.path),
                    path=["", "", metric.path[3], metric.path[3]],
                    value=value,
                    multi=True,
                )

    @metrics(["Environment | Voltage"], volatile=False, access="S")  # SNMP version
    def get_voltage(self, metrics):
        for metric in metrics:
            if metric.ifindex == 29:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.40.0")
                self.set_metric(
                    id=("Environment | Voltage", metric.path),
                    path=["", "", "battery", metric.path[3]],
                    value=value,
                    scale=scale(0.1, 2),
                    multi=True,
                )

    @metrics(["Environment | Power | Input | Status"], volatile=False, access="S")  # SNMP version
    def get_power_input_status(self, metrics):
        for metric in metrics:
            value = 1
            if metric.ifindex == 29:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.27.0")
            elif metric.ifindex == 3:
                s_type = self.snmp.get("1.3.6.1.4.1.51315.1.15.0")
                status = self.snmp.get("1.3.6.1.4.1.51315.1.%s.0" % metric.ifindex)
                if s_type == 0 and status == 0:
                    value = 0
            self.set_metric(
                id=("Environment | Power | Input | Status", metric.path),
                value=value,
            )

    @metrics(["Environment | Electric Current"], volatile=False, access="S")  # SNMP version
    def get_current_input(self, metrics):
        for metric in metrics:
            if metric.ifindex == 3:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.19")
                self.set_metric(id=("Environment | Electric Current", metric.path), value=value)

    @metrics(["Environment | Energy Consumption"], volatile=False, access="S")  # SNMP version
    def get_energy_cons(self, metrics):
        for metric in metrics:
            if metric.ifindex == 26:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.25.0")
                self.set_metric(
                    id=("Environment | Energy Consumption", metric.path),
                    value=value,
                )

    @metrics(
        ["Environment | Battery | Capacity | Level"], volatile=False, access="S"
    )  # SNMP version
    def get_battery_capacity(self, metrics):
        for metric in metrics:
            if metric.ifindex == 29:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.41.0")
                self.set_metric(
                    id=("Environment | Battery | Capacity | Level", metric.path),
                    value=value,
                )

    @metrics(["Environment | Pulse"], volatile=False, access="S")  # SNMP version
    def get_pulse(self, metrics):
        for metric in metrics:
            if metric.ifindex == 6:
                value = self.snmp.get("1.3.6.1.4.1.51315.1.8.0")
                self.set_metric(
                    id=("Environment | Pulse", metric.path),
                    path=["", "", "", metric.path[3]],
                    value=value,
                )
