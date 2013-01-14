# -*- coding: utf-8 -*-
##----------------------------------------------------------------------
## DLink.DxS.get_license test
## Auto-generated by ./noc debug-script at 14.01.2013 16:14:46
##----------------------------------------------------------------------
## Copyright (C) 2007-2013 The NOC Project
## See LICENSE for details
##----------------------------------------------------------------------

## NOC modules
from noc.lib.test import ScriptTestCase


class DLink_DxS_get_license_Test(ScriptTestCase):
    script = "DLink.DxS.get_license"
    vendor = "DLink"
    platform = "DGS-3620-28SC"
    version = "2.00.B041"
    input = {}
    result = {'license': 'EI'}
    motd = ''
    cli = {
## 'show dlms license'
'show dlms license': """show dlms license
Command: show dlms license

Device Default License : EI


""", 
## 'show switch'
'show switch': """show switch
Command: show switch

Device Type                : DGS-3620-28SC Gigabit Ethernet Switch
MAC Address                : 84-C9-B2-1C-6A-00
IP Address                 : 192.168.100.1 (Manual)
VLAN Name                  : default
Subnet Mask                : 255.255.255.0
Default Gateway            : 0.0.0.0
Boot PROM Version          : Build 1.00.016
Firmware Version           : Build 2.00.B041
Hardware Version           : A1
Firmware Type              : EI
Serial Number              : PVXE1B9000287
System Name                : 
System Location            : Souzinform
System Uptime              : 4 days, 0 hours, 19 minutes, 55 seconds
System Contact             : 
Spanning Tree              : Disabled
GVRP                       : Disabled
IGMP Snooping              : Disabled
MLD Snooping               : Disabled
RIP                        : Disabled
RIPng                      : Disabled
DVMRP                      : Disabled
PIM                        : Disabled
PIM6                       : Disabled
OSPF                       : Disabled
OSPFv3                     : Disabled
BGP   \t                   : Enabled
VLAN Trunk                 : Disabled
Telnet                     : Disabled
Web                        : Disabled
SNMP                       : Disabled
SSL Status                 : Disabled
SSH Status                 : Enabled
802.1X                     : Disabled
Jumbo Frame                : Off
CLI Paging                 : Disabled
MAC Notification           : Disabled
Port Mirror                : Disabled
SNTP                       : Disabled
DHCP Relay                 : Enabled
DNSR Status                : Disabled 
VRRP                       : Disabled
HOL Prevention State       : Enabled
Syslog Global State        : Disabled
Single IP Management       : Disabled
Password Encryption Status : Enabled
DNS Resolver               : Disabled
""", 
}
    snmp_get = {}
    snmp_getnext = {}
    http_get = {}
