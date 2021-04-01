# ---------------------------------------------------------------------
# Juniper.JUNOS.SlotRule
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# NOC modules
from noc.sa.profiles.Generic.get_metrics import OIDRule
from noc.core.mib import mib


class SlotRule(OIDRule):
    name = "slot"

    def iter_oids(self, script, metric):
        """
        SlotName:
        Routing Engine
        PIC
        FPC
        MIC
        :param metrics:
        :return:
        """
        for i, desc in script.snmp.getnext("1.3.6.1.4.1.2636.3.1.13.1.5"):
            if desc.startswith("PIC:") or desc in ["midplane", "FPM Board"]:
                # `midplane` and `FPM Board` always return zero
                # PIC partially duplicate velues with FPC
                continue
            slotid = i[len("1.3.6.1.4.1.2636.3.1.13.1.5") + 1 :]
            oid = mib[self.expand(self.oid, {"hwSlotIndex": slotid})]
            if "MS-MIC" in desc or "MS-MPC" in desc or "MS-DPC" in desc:
                if "CPU" in metric.metric or "Environment" in metric.metric:
                    if "Temperature" in metric.metric and "Environment" in metric.metric:
                        desc = "Temperature " + desc
                    labels = [
                        f"noc::chassis::{int(slotid.split('.')[1]) - 1}",
                        f"noc::slot::{int(slotid.split('.')[2]) - 1}",
                        f"noc::module::{slotid.split('.')[3]}",
                        f"noc::sensor::{desc}"
                        if "Environment" in metric.metric
                        else f"noc::cpu::{desc}",
                    ]
                else:
                    labels = [int(slotid.split(".")[1]) - 1, int(slotid.split(".")[2]) - 1, desc]
                yield oid, self.type, self.scale, labels
            elif desc.startswith("MIC:"):
                # Only MS modules return values in this slot
                continue
            elif "FPC" in desc:
                if "CPU" in metric.metric or "Environment" in metric.metric:
                    if "Temperature" in metric.metric and "Environment" in metric.metric:
                        desc = "Temperature " + desc
                    labels = [
                        f"noc::chassis::{int(slotid.split('.')[1]) - 1}",
                        f"noc::slot::{slotid.split('.')[2]}",
                        f"noc::module::{slotid.split('.')[3]}",
                        f"noc::sensor::{desc}"
                        if "Environment" in metric.metric
                        else f"noc::cpu::{desc}",
                    ]
                else:
                    labels = [int(slotid.split(".")[1]) - 1, slotid.split(".")[2], desc]
                yield oid, self.type, self.scale, labels
            elif "Routing Engine" in desc:
                if "CPU" in metric.metric or "Environment" in metric.metric:
                    if "Temperature" in metric.metric and "Environment" in metric.metric:
                        desc = "Temperature " + desc
                    labels = [
                        f"noc::chassis::{slotid.split('.')[1]}",
                        f"noc::slot::{slotid.split('.')[2]}",
                        f"noc::module::{slotid.split('.')[3]}",
                        f"noc::sensor::{desc}"
                        if "Environment" in metric.metric
                        else f"noc::cpu::{desc}",
                    ]
                else:
                    labels = [int(slotid.split(".")[1]), int(slotid.split(".")[2]), desc]
                yield oid, self.type, self.scale, labels
            else:
                if "Environment" in metric.metric:
                    if "Temperature" in metric.metric:
                        desc = "Temperature " + desc
                    labels = [
                        f"noc::chassis::{slotid.split('.')[1]}",
                        f"noc::slot::{slotid.split('.')[2]}",
                        f"noc::module::{slotid.split('.')[3]}",
                        f"noc::sensor::{desc}"
                        if "Environment" in metric.metric
                        else f"noc::cpu::{desc}",
                    ]
                    yield oid, self.type, self.scale, labels
