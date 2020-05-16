# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Python modules
import re

# NOC modules
from noc.core.script.base import BaseScript
from noc.sa.interfaces.igetversion import IGetVersion
from noc.core.text import strip_html_tags
from noc.core.comp import smart_text


class Script(BaseScript):
    name = "TFortis.PSW.get_version"
    cache = True
    interface = IGetVersion

    rx_html_ver = re.compile(
        r"Firmware version(?P<version>.*)Bootloader version(?P<bootloader>.*)\sMAC"
    )
    rx_html_platform = re.compile(r"^TFortis (?P<platform>.*)\x00")
    rx_html_platform2 = re.compile(r"(?P<platform>PSW-\S+)")

    def execute(self):
        v = self.http.get("/header_name.shtml", eof_mark=b"</html>")
        v = strip_html_tags(v)
        platform = self.rx_html_platform.search(v)
        if not platform:
            platform = self.rx_html_platform2.search(v)
        v = self.http.get("/main.shtml", eof_mark=b"</html>")
        v = strip_html_tags(v)
        match = self.rx_html_ver.search(v)
        return {
            "vendor": "TFortis",
            "platform": platform.group("platform").strip(smart_text("\x00")),
            "version": match.group("version"),
            "attributes": {"Bootloader": match.group("bootloader")},
        }
