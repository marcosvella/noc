# ---------------------------------------------------------------------
# Qtech.BFC_PBIC_S.get_metrics
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import Script as GetMetricsScript, metrics
from core.script.metrics import scale


class Script(GetMetricsScript):
    name = "Qtech.BFC_PBIC_S.get_metrics"

    def get_battery(self):
        for oid, key in self.snmp.getnext("1.3.6.1.3.55.1.3.1.1", max_retries=3, cached=True):
            b_descr = self.snmp.get("1.3.6.1.3.55.1.3.1.2.%s" % key)
            if b_descr == 9:
                b_status = self.snmp.get("1.3.6.1.3.55.1.3.1.4.%s" % key)
                b_invert = self.snmp.get("1.3.6.1.3.55.1.3.1.3.%s" % key)
                if b_invert == 0 and b_status == 0:
                    return True
                elif b_invert == 1 and b_status == 1:
                    return True
                elif b_invert == 0 and b_status == 1:
                    return True
                elif b_invert == 1 and b_status == 0:
                    return True

    @metrics(["Environment | Sensor Status"], volatile=False, access="S")  # SNMP version
    def get_interface_admin_status(self, metrics):
        for metric in metrics:
            if metric.ifindex == 100:
                continue
            value = 1
            descr = self.snmp.get("1.3.6.1.3.55.1.3.1.2.%s" % metric.ifindex)
            status = self.snmp.get("1.3.6.1.3.55.1.3.1.4.%s" % metric.ifindex)
            invert = self.snmp.get("1.3.6.1.3.55.1.3.1.3.%s" % metric.ifindex)
            if descr in [0, 3]:
                if invert == 0 and status == 0:
                    value = 0
                elif invert == 1 and status == 1:
                    value = 0
            elif descr in [9, 10]:
                if descr == 9:
                    if invert == 0 and status == 0:
                        value = 0
                    elif invert == 1 and status == 1:
                        value = 0
                    elif invert == 0 and status == 1:
                        value = 0
                    elif invert == 1 and status == 0:
                        value = 0
                if descr == 10:
                    battery = self.get_battery()
                    if battery and invert == 0 and status == 0:
                        value = 0
                    elif battery and invert == 1 and status == 1:
                        value = 0
            else:
                if status > 0:
                    value = 0
            if len(str(metric.ifindex)) == 2:
                ifindex = list(str(metric.ifindex))
                temp = self.snmp.get("1.3.6.1.3.55.1.%s.%s.0" % (ifindex[0], ifindex[1]))
                if -55 < temp < 600:
                    value = 0
            self.set_metric(
                id=("Environment | Sensor Status", metric.path), value=value,
            )

    @metrics(["Environment | Temperature"], volatile=False, access="S")  # SNMP version
    def get_temperature(self, metrics):
        for metric in metrics:
            ifindex = list(str(metric.ifindex))
            value = self.snmp.get("1.3.6.1.3.55.1.%s.%s.0" % (ifindex[0], ifindex[1]))
            self.set_metric(
                id=("Environment | Temperature", metric.path),
                path=["", "", metric.path[3], metric.path[3]],
                value=value,
                multi=True,
            )

    @metrics(["Environment | Voltage"], volatile=False, access="S")  # SNMP version
    def get_voltage(self, metrics):
        for metric in metrics:
            value = self.snmp.get("1.3.6.1.3.55.1.3.1.4.%s" % metric.ifindex)
            self.set_metric(
                id=("Environment | Voltage", metric.path),
                path=["", "", metric.path[3], metric.path[3]],
                value=value,
                scale=scale(0.001, 2),
                multi=True,
            )

    @metrics(["Environment | Power | Input | Status"], volatile=False, access="S")  # SNMP version
    def get_power_input_status(self, metrics):
        for metric in metrics:
            value = 1
            descr = self.snmp.get("1.3.6.1.3.55.1.3.1.2.%s" % metric.ifindex)
            if descr == 10:
                status = self.snmp.get("1.3.6.1.3.55.1.3.1.4.%s" % metric.ifindex)
                invert = self.snmp.get("1.3.6.1.3.55.1.3.1.3.%s" % metric.ifindex)
                battery = self.get_battery()
                if battery and invert == 0 and status == 0:
                    value = 0
                elif battery and invert == 1 and status == 1:
                    value = 0
                self.set_metric(
                    id=("Environment | Power | Input | Status", metric.path), value=value,
                )
