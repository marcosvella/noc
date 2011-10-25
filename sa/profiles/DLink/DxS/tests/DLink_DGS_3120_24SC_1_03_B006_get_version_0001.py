# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## DLink.DxS.get_version test
## Auto-generated by ./noc debug-script at 2011-10-25 10:01:24
##----------------------------------------------------------------------
## Copyright (C) 2007-2011 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------

## NOC modules
from noc.lib.test import ScriptTestCase


class DLink_DxS_get_version_Test(ScriptTestCase):
    script = "DLink.DxS.get_version"
    vendor = "DLink"
    platform = 'DGS-3120-24SC'
    version = '1.03.B006'
    input = {}
    result = {'attributes': {'Boot PROM': '1.00.009',
                'Firmware Type': 'EI',
                'HW version': 'A1',
                'Serial Number': 'P4XD1B2000676'},
 'platform': 'DGS-3120-24SC',
 'vendor': 'DLink',
 'version': '1.03.B006'}
    motd = '\n                    DGS-3120-24SC Gigabit Ethernet Switch\n                            Command Line Interface\n\n                          Firmware: Build 1.03.B006\n           Copyright(C) 2011 D-Link Corporation. All rights reserved.\n\n'
    cli = {
## 'show switch'
'show switch': """show switch
Command: show switch

Device Type                : DGS-3120-24SC Gigabit Ethernet Switch
Unit ID                    : 1
MAC Address                : 5C-D9-98-CA-27-36
IP Address                 : 10.116.0.201 (Manual)
VLAN Name                  : upr
Subnet Mask                : 255.255.0.0
Default Gateway            : 10.116.0.1
Boot PROM Version          : Build 1.00.009
Firmware Version           : Build 1.03.B006
Hardware Version           : A1
Firmware Type              : EI
Serial Number              : P4XD1B2000676
System Name                : 
System Location            : Servernaya1
System Uptime              : 23 days, 17 hours, 42 minutes, 46 seconds
System Contact             : 
Spanning Tree              : Disabled
GVRP                       : Disabled
IGMP Snooping              : Disabled
MLD Snooping               : Disabled
VLAN Trunk                 : Disabled
Telnet                     : Enabled (TCP 23)
                                                                                                     
Web                        : Disabled
SNMP                       : Enabled
SSL Status                 : Disabled
SSH Status                 : Enabled
802.1x                     : Disabled
Jumbo Frame                : Off
CLI Paging                 : Enabled
MAC Notification           : Disabled
Port Mirror                : Disabled
SNTP                       : Enabled
HOL Prevention State       : Enabled
Syslog Global State        : Disabled
Single IP Management       : Disabled
Password Encryption Status : Enabled
""", 
## 'disable clipaging'
'disable clipaging': """disable clipaging
Command: disable clipaging

Success.                                                          
""", 
## 'enable clipaging'
'enable clipaging': """enable clipaging
Command: enable clipaging

Success.                                                          
""", 
}
    snmp_get = {}
    snmp_getnext = {}
