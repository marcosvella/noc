# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# CISCO-VTP-MIB
# Compiled MIB
# Do not modify this file directly
# Run ./noc mib make-cmib instead
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# MIB Name
NAME = "CISCO-VTP-MIB"

# Metadata
LAST_UPDATED = "2010-05-12"
COMPILED = "2020-01-19"

# MIB Data: name -> oid
MIB = {
    "CISCO-VTP-MIB::ciscoVtpMIB": "1.3.6.1.4.1.9.9.46",
    "CISCO-VTP-MIB::vtpMIBObjects": "1.3.6.1.4.1.9.9.46.1",
    "CISCO-VTP-MIB::vtpStatus": "1.3.6.1.4.1.9.9.46.1.1",
    "CISCO-VTP-MIB::vtpVersion": "1.3.6.1.4.1.9.9.46.1.1.1",
    "CISCO-VTP-MIB::vtpMaxVlanStorage": "1.3.6.1.4.1.9.9.46.1.1.2",
    "CISCO-VTP-MIB::vtpNotificationsEnabled": "1.3.6.1.4.1.9.9.46.1.1.3",
    "CISCO-VTP-MIB::vtpVlanCreatedNotifEnabled": "1.3.6.1.4.1.9.9.46.1.1.4",
    "CISCO-VTP-MIB::vtpVlanDeletedNotifEnabled": "1.3.6.1.4.1.9.9.46.1.1.5",
    "CISCO-VTP-MIB::vlanManagementDomains": "1.3.6.1.4.1.9.9.46.1.2",
    "CISCO-VTP-MIB::managementDomainTable": "1.3.6.1.4.1.9.9.46.1.2.1",
    "CISCO-VTP-MIB::managementDomainEntry": "1.3.6.1.4.1.9.9.46.1.2.1.1",
    "CISCO-VTP-MIB::managementDomainIndex": "1.3.6.1.4.1.9.9.46.1.2.1.1.1",
    "CISCO-VTP-MIB::managementDomainName": "1.3.6.1.4.1.9.9.46.1.2.1.1.2",
    "CISCO-VTP-MIB::managementDomainLocalMode": "1.3.6.1.4.1.9.9.46.1.2.1.1.3",
    "CISCO-VTP-MIB::managementDomainConfigRevNumber": "1.3.6.1.4.1.9.9.46.1.2.1.1.4",
    "CISCO-VTP-MIB::managementDomainLastUpdater": "1.3.6.1.4.1.9.9.46.1.2.1.1.5",
    "CISCO-VTP-MIB::managementDomainLastChange": "1.3.6.1.4.1.9.9.46.1.2.1.1.6",
    "CISCO-VTP-MIB::managementDomainRowStatus": "1.3.6.1.4.1.9.9.46.1.2.1.1.7",
    "CISCO-VTP-MIB::managementDomainTftpServer": "1.3.6.1.4.1.9.9.46.1.2.1.1.8",
    "CISCO-VTP-MIB::managementDomainTftpPathname": "1.3.6.1.4.1.9.9.46.1.2.1.1.9",
    "CISCO-VTP-MIB::managementDomainPruningState": "1.3.6.1.4.1.9.9.46.1.2.1.1.10",
    "CISCO-VTP-MIB::managementDomainVersionInUse": "1.3.6.1.4.1.9.9.46.1.2.1.1.11",
    "CISCO-VTP-MIB::managementDomainPruningStateOper": "1.3.6.1.4.1.9.9.46.1.2.1.1.12",
    "CISCO-VTP-MIB::vlanInfo": "1.3.6.1.4.1.9.9.46.1.3",
    "CISCO-VTP-MIB::vtpVlanTable": "1.3.6.1.4.1.9.9.46.1.3.1",
    "CISCO-VTP-MIB::vtpVlanEntry": "1.3.6.1.4.1.9.9.46.1.3.1.1",
    "CISCO-VTP-MIB::vtpVlanIndex": "1.3.6.1.4.1.9.9.46.1.3.1.1.1",
    "CISCO-VTP-MIB::vtpVlanState": "1.3.6.1.4.1.9.9.46.1.3.1.1.2",
    "CISCO-VTP-MIB::vtpVlanType": "1.3.6.1.4.1.9.9.46.1.3.1.1.3",
    "CISCO-VTP-MIB::vtpVlanName": "1.3.6.1.4.1.9.9.46.1.3.1.1.4",
    "CISCO-VTP-MIB::vtpVlanMtu": "1.3.6.1.4.1.9.9.46.1.3.1.1.5",
    "CISCO-VTP-MIB::vtpVlanDot10Said": "1.3.6.1.4.1.9.9.46.1.3.1.1.6",
    "CISCO-VTP-MIB::vtpVlanRingNumber": "1.3.6.1.4.1.9.9.46.1.3.1.1.7",
    "CISCO-VTP-MIB::vtpVlanBridgeNumber": "1.3.6.1.4.1.9.9.46.1.3.1.1.8",
    "CISCO-VTP-MIB::vtpVlanStpType": "1.3.6.1.4.1.9.9.46.1.3.1.1.9",
    "CISCO-VTP-MIB::vtpVlanParentVlan": "1.3.6.1.4.1.9.9.46.1.3.1.1.10",
    "CISCO-VTP-MIB::vtpVlanTranslationalVlan1": "1.3.6.1.4.1.9.9.46.1.3.1.1.11",
    "CISCO-VTP-MIB::vtpVlanTranslationalVlan2": "1.3.6.1.4.1.9.9.46.1.3.1.1.12",
    "CISCO-VTP-MIB::vtpVlanBridgeType": "1.3.6.1.4.1.9.9.46.1.3.1.1.13",
    "CISCO-VTP-MIB::vtpVlanAreHopCount": "1.3.6.1.4.1.9.9.46.1.3.1.1.14",
    "CISCO-VTP-MIB::vtpVlanSteHopCount": "1.3.6.1.4.1.9.9.46.1.3.1.1.15",
    "CISCO-VTP-MIB::vtpVlanIsCRFBackup": "1.3.6.1.4.1.9.9.46.1.3.1.1.16",
    "CISCO-VTP-MIB::vtpVlanTypeExt": "1.3.6.1.4.1.9.9.46.1.3.1.1.17",
    "CISCO-VTP-MIB::vtpVlanIfIndex": "1.3.6.1.4.1.9.9.46.1.3.1.1.18",
    "CISCO-VTP-MIB::internalVlanInfo": "1.3.6.1.4.1.9.9.46.1.3.2",
    "CISCO-VTP-MIB::vtpInternalVlanAllocPolicy": "1.3.6.1.4.1.9.9.46.1.3.2.1",
    "CISCO-VTP-MIB::vtpInternalVlanTable": "1.3.6.1.4.1.9.9.46.1.3.2.2",
    "CISCO-VTP-MIB::vtpInternalVlanEntry": "1.3.6.1.4.1.9.9.46.1.3.2.2.1",
    "CISCO-VTP-MIB::vtpInternalVlanOwner": "1.3.6.1.4.1.9.9.46.1.3.2.2.1.1",
    "CISCO-VTP-MIB::vlanEdit": "1.3.6.1.4.1.9.9.46.1.4",
    "CISCO-VTP-MIB::vtpEditControlTable": "1.3.6.1.4.1.9.9.46.1.4.1",
    "CISCO-VTP-MIB::vtpEditControlEntry": "1.3.6.1.4.1.9.9.46.1.4.1.1",
    "CISCO-VTP-MIB::vtpVlanEditOperation": "1.3.6.1.4.1.9.9.46.1.4.1.1.1",
    "CISCO-VTP-MIB::vtpVlanApplyStatus": "1.3.6.1.4.1.9.9.46.1.4.1.1.2",
    "CISCO-VTP-MIB::vtpVlanEditBufferOwner": "1.3.6.1.4.1.9.9.46.1.4.1.1.3",
    "CISCO-VTP-MIB::vtpVlanEditConfigRevNumber": "1.3.6.1.4.1.9.9.46.1.4.1.1.4",
    "CISCO-VTP-MIB::vtpVlanEditModifiedVlan": "1.3.6.1.4.1.9.9.46.1.4.1.1.5",
    "CISCO-VTP-MIB::vtpVlanEditTable": "1.3.6.1.4.1.9.9.46.1.4.2",
    "CISCO-VTP-MIB::vtpVlanEditEntry": "1.3.6.1.4.1.9.9.46.1.4.2.1",
    "CISCO-VTP-MIB::vtpVlanEditIndex": "1.3.6.1.4.1.9.9.46.1.4.2.1.1",
    "CISCO-VTP-MIB::vtpVlanEditState": "1.3.6.1.4.1.9.9.46.1.4.2.1.2",
    "CISCO-VTP-MIB::vtpVlanEditType": "1.3.6.1.4.1.9.9.46.1.4.2.1.3",
    "CISCO-VTP-MIB::vtpVlanEditName": "1.3.6.1.4.1.9.9.46.1.4.2.1.4",
    "CISCO-VTP-MIB::vtpVlanEditMtu": "1.3.6.1.4.1.9.9.46.1.4.2.1.5",
    "CISCO-VTP-MIB::vtpVlanEditDot10Said": "1.3.6.1.4.1.9.9.46.1.4.2.1.6",
    "CISCO-VTP-MIB::vtpVlanEditRingNumber": "1.3.6.1.4.1.9.9.46.1.4.2.1.7",
    "CISCO-VTP-MIB::vtpVlanEditBridgeNumber": "1.3.6.1.4.1.9.9.46.1.4.2.1.8",
    "CISCO-VTP-MIB::vtpVlanEditStpType": "1.3.6.1.4.1.9.9.46.1.4.2.1.9",
    "CISCO-VTP-MIB::vtpVlanEditParentVlan": "1.3.6.1.4.1.9.9.46.1.4.2.1.10",
    "CISCO-VTP-MIB::vtpVlanEditRowStatus": "1.3.6.1.4.1.9.9.46.1.4.2.1.11",
    "CISCO-VTP-MIB::vtpVlanEditTranslationalVlan1": "1.3.6.1.4.1.9.9.46.1.4.2.1.12",
    "CISCO-VTP-MIB::vtpVlanEditTranslationalVlan2": "1.3.6.1.4.1.9.9.46.1.4.2.1.13",
    "CISCO-VTP-MIB::vtpVlanEditBridgeType": "1.3.6.1.4.1.9.9.46.1.4.2.1.14",
    "CISCO-VTP-MIB::vtpVlanEditAreHopCount": "1.3.6.1.4.1.9.9.46.1.4.2.1.15",
    "CISCO-VTP-MIB::vtpVlanEditSteHopCount": "1.3.6.1.4.1.9.9.46.1.4.2.1.16",
    "CISCO-VTP-MIB::vtpVlanEditIsCRFBackup": "1.3.6.1.4.1.9.9.46.1.4.2.1.17",
    "CISCO-VTP-MIB::vtpVlanEditTypeExt": "1.3.6.1.4.1.9.9.46.1.4.2.1.18",
    "CISCO-VTP-MIB::vtpVlanEditTypeExt2": "1.3.6.1.4.1.9.9.46.1.4.2.1.19",
    "CISCO-VTP-MIB::vtpStats": "1.3.6.1.4.1.9.9.46.1.5",
    "CISCO-VTP-MIB::vtpStatsTable": "1.3.6.1.4.1.9.9.46.1.5.1",
    "CISCO-VTP-MIB::vtpStatsEntry": "1.3.6.1.4.1.9.9.46.1.5.1.1",
    "CISCO-VTP-MIB::vtpInSummaryAdverts": "1.3.6.1.4.1.9.9.46.1.5.1.1.1",
    "CISCO-VTP-MIB::vtpInSubsetAdverts": "1.3.6.1.4.1.9.9.46.1.5.1.1.2",
    "CISCO-VTP-MIB::vtpInAdvertRequests": "1.3.6.1.4.1.9.9.46.1.5.1.1.3",
    "CISCO-VTP-MIB::vtpOutSummaryAdverts": "1.3.6.1.4.1.9.9.46.1.5.1.1.4",
    "CISCO-VTP-MIB::vtpOutSubsetAdverts": "1.3.6.1.4.1.9.9.46.1.5.1.1.5",
    "CISCO-VTP-MIB::vtpOutAdvertRequests": "1.3.6.1.4.1.9.9.46.1.5.1.1.6",
    "CISCO-VTP-MIB::vtpConfigRevNumberErrors": "1.3.6.1.4.1.9.9.46.1.5.1.1.7",
    "CISCO-VTP-MIB::vtpConfigDigestErrors": "1.3.6.1.4.1.9.9.46.1.5.1.1.8",
    "CISCO-VTP-MIB::vlanTrunkPorts": "1.3.6.1.4.1.9.9.46.1.6",
    "CISCO-VTP-MIB::vlanTrunkPortTable": "1.3.6.1.4.1.9.9.46.1.6.1",
    "CISCO-VTP-MIB::vlanTrunkPortEntry": "1.3.6.1.4.1.9.9.46.1.6.1.1",
    "CISCO-VTP-MIB::vlanTrunkPortIfIndex": "1.3.6.1.4.1.9.9.46.1.6.1.1.1",
    "CISCO-VTP-MIB::vlanTrunkPortManagementDomain": "1.3.6.1.4.1.9.9.46.1.6.1.1.2",
    "CISCO-VTP-MIB::vlanTrunkPortEncapsulationType": "1.3.6.1.4.1.9.9.46.1.6.1.1.3",
    "CISCO-VTP-MIB::vlanTrunkPortVlansEnabled": "1.3.6.1.4.1.9.9.46.1.6.1.1.4",
    "CISCO-VTP-MIB::vlanTrunkPortNativeVlan": "1.3.6.1.4.1.9.9.46.1.6.1.1.5",
    "CISCO-VTP-MIB::vlanTrunkPortRowStatus": "1.3.6.1.4.1.9.9.46.1.6.1.1.6",
    "CISCO-VTP-MIB::vlanTrunkPortInJoins": "1.3.6.1.4.1.9.9.46.1.6.1.1.7",
    "CISCO-VTP-MIB::vlanTrunkPortOutJoins": "1.3.6.1.4.1.9.9.46.1.6.1.1.8",
    "CISCO-VTP-MIB::vlanTrunkPortOldAdverts": "1.3.6.1.4.1.9.9.46.1.6.1.1.9",
    "CISCO-VTP-MIB::vlanTrunkPortVlansPruningEligible": "1.3.6.1.4.1.9.9.46.1.6.1.1.10",
    "CISCO-VTP-MIB::vlanTrunkPortVlansXmitJoined": "1.3.6.1.4.1.9.9.46.1.6.1.1.11",
    "CISCO-VTP-MIB::vlanTrunkPortVlansRcvJoined": "1.3.6.1.4.1.9.9.46.1.6.1.1.12",
    "CISCO-VTP-MIB::vlanTrunkPortDynamicState": "1.3.6.1.4.1.9.9.46.1.6.1.1.13",
    "CISCO-VTP-MIB::vlanTrunkPortDynamicStatus": "1.3.6.1.4.1.9.9.46.1.6.1.1.14",
    "CISCO-VTP-MIB::vlanTrunkPortVtpEnabled": "1.3.6.1.4.1.9.9.46.1.6.1.1.15",
    "CISCO-VTP-MIB::vlanTrunkPortEncapsulationOperType": "1.3.6.1.4.1.9.9.46.1.6.1.1.16",
    "CISCO-VTP-MIB::vlanTrunkPortVlansEnabled2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.17",
    "CISCO-VTP-MIB::vlanTrunkPortVlansEnabled3k": "1.3.6.1.4.1.9.9.46.1.6.1.1.18",
    "CISCO-VTP-MIB::vlanTrunkPortVlansEnabled4k": "1.3.6.1.4.1.9.9.46.1.6.1.1.19",
    "CISCO-VTP-MIB::vtpVlansPruningEligible2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.20",
    "CISCO-VTP-MIB::vtpVlansPruningEligible3k": "1.3.6.1.4.1.9.9.46.1.6.1.1.21",
    "CISCO-VTP-MIB::vtpVlansPruningEligible4k": "1.3.6.1.4.1.9.9.46.1.6.1.1.22",
    "CISCO-VTP-MIB::vlanTrunkPortVlansXmitJoined2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.23",
    "CISCO-VTP-MIB::vlanTrunkPortVlansXmitJoined3k": "1.3.6.1.4.1.9.9.46.1.6.1.1.24",
    "CISCO-VTP-MIB::vlanTrunkPortVlansXmitJoined4k": "1.3.6.1.4.1.9.9.46.1.6.1.1.25",
    "CISCO-VTP-MIB::vlanTrunkPortVlansRcvJoined2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.26",
    "CISCO-VTP-MIB::vlanTrunkPortVlansRcvJoined3k": "1.3.6.1.4.1.9.9.46.1.6.1.1.27",
    "CISCO-VTP-MIB::vlanTrunkPortVlansRcvJoined4k": "1.3.6.1.4.1.9.9.46.1.6.1.1.28",
    "CISCO-VTP-MIB::vlanTrunkPortDot1qTunnel": "1.3.6.1.4.1.9.9.46.1.6.1.1.29",
    "CISCO-VTP-MIB::vlanTrunkPortVlansActiveFirst2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.30",
    "CISCO-VTP-MIB::vlanTrunkPortVlansActiveSecond2k": "1.3.6.1.4.1.9.9.46.1.6.1.1.31",
    "CISCO-VTP-MIB::vlanTrunkPortSetSerialNo": "1.3.6.1.4.1.9.9.46.1.6.2",
    "CISCO-VTP-MIB::vlanTrunkPortsDot1qTag": "1.3.6.1.4.1.9.9.46.1.6.3",
    "CISCO-VTP-MIB::vtpDiscover": "1.3.6.1.4.1.9.9.46.1.7",
    "CISCO-VTP-MIB::vtpDiscoverTable": "1.3.6.1.4.1.9.9.46.1.7.1",
    "CISCO-VTP-MIB::vtpDiscoverEntry": "1.3.6.1.4.1.9.9.46.1.7.1.1",
    "CISCO-VTP-MIB::vtpDiscoverAction": "1.3.6.1.4.1.9.9.46.1.7.1.1.1",
    "CISCO-VTP-MIB::vtpDiscoverStatus": "1.3.6.1.4.1.9.9.46.1.7.1.1.2",
    "CISCO-VTP-MIB::vtpLastDiscoverTime": "1.3.6.1.4.1.9.9.46.1.7.1.1.3",
    "CISCO-VTP-MIB::vtpDiscoverResultTable": "1.3.6.1.4.1.9.9.46.1.7.2",
    "CISCO-VTP-MIB::vtpDiscoverResultEntry": "1.3.6.1.4.1.9.9.46.1.7.2.1",
    "CISCO-VTP-MIB::vtpDiscoverResultIndex": "1.3.6.1.4.1.9.9.46.1.7.2.1.1",
    "CISCO-VTP-MIB::vtpDiscoverResultDatabaseName": "1.3.6.1.4.1.9.9.46.1.7.2.1.2",
    "CISCO-VTP-MIB::vtpDiscoverResultConflicting": "1.3.6.1.4.1.9.9.46.1.7.2.1.3",
    "CISCO-VTP-MIB::vtpDiscoverResultDeviceId": "1.3.6.1.4.1.9.9.46.1.7.2.1.4",
    "CISCO-VTP-MIB::vtpDiscoverResultPrimaryServer": "1.3.6.1.4.1.9.9.46.1.7.2.1.5",
    "CISCO-VTP-MIB::vtpDiscoverResultRevNumber": "1.3.6.1.4.1.9.9.46.1.7.2.1.6",
    "CISCO-VTP-MIB::vtpDiscoverResultSystemName": "1.3.6.1.4.1.9.9.46.1.7.2.1.7",
    "CISCO-VTP-MIB::vtpDatabase": "1.3.6.1.4.1.9.9.46.1.8",
    "CISCO-VTP-MIB::vtpDatabaseTable": "1.3.6.1.4.1.9.9.46.1.8.1",
    "CISCO-VTP-MIB::vtpDatabaseEntry": "1.3.6.1.4.1.9.9.46.1.8.1.1",
    "CISCO-VTP-MIB::vtpDatabaseIndex": "1.3.6.1.4.1.9.9.46.1.8.1.1.1",
    "CISCO-VTP-MIB::vtpDatabaseName": "1.3.6.1.4.1.9.9.46.1.8.1.1.2",
    "CISCO-VTP-MIB::vtpDatabaseLocalMode": "1.3.6.1.4.1.9.9.46.1.8.1.1.3",
    "CISCO-VTP-MIB::vtpDatabaseRevNumber": "1.3.6.1.4.1.9.9.46.1.8.1.1.4",
    "CISCO-VTP-MIB::vtpDatabasePrimaryServer": "1.3.6.1.4.1.9.9.46.1.8.1.1.5",
    "CISCO-VTP-MIB::vtpDatabasePrimaryServerId": "1.3.6.1.4.1.9.9.46.1.8.1.1.6",
    "CISCO-VTP-MIB::vtpDatabaseTakeOverPrimary": "1.3.6.1.4.1.9.9.46.1.8.1.1.7",
    "CISCO-VTP-MIB::vtpDatabaseTakeOverPassword": "1.3.6.1.4.1.9.9.46.1.8.1.1.8",
    "CISCO-VTP-MIB::vtpAuthentication": "1.3.6.1.4.1.9.9.46.1.9",
    "CISCO-VTP-MIB::vtpAuthenticationTable": "1.3.6.1.4.1.9.9.46.1.9.1",
    "CISCO-VTP-MIB::vtpAuthEntry": "1.3.6.1.4.1.9.9.46.1.9.1.1",
    "CISCO-VTP-MIB::vtpAuthPassword": "1.3.6.1.4.1.9.9.46.1.9.1.1.1",
    "CISCO-VTP-MIB::vtpAuthPasswordType": "1.3.6.1.4.1.9.9.46.1.9.1.1.2",
    "CISCO-VTP-MIB::vtpAuthSecretKey": "1.3.6.1.4.1.9.9.46.1.9.1.1.3",
    "CISCO-VTP-MIB::vlanStatistics": "1.3.6.1.4.1.9.9.46.1.10",
    "CISCO-VTP-MIB::vlanStatsVlans": "1.3.6.1.4.1.9.9.46.1.10.1",
    "CISCO-VTP-MIB::vlanStatsExtendedVlans": "1.3.6.1.4.1.9.9.46.1.10.2",
    "CISCO-VTP-MIB::vlanStatsInternalVlans": "1.3.6.1.4.1.9.9.46.1.10.3",
    "CISCO-VTP-MIB::vlanStatsFreeVlans": "1.3.6.1.4.1.9.9.46.1.10.4",
    "CISCO-VTP-MIB::vtpNotifications": "1.3.6.1.4.1.9.9.46.2",
    "CISCO-VTP-MIB::vtpNotificationsPrefix": "1.3.6.1.4.1.9.9.46.2.0",
    "CISCO-VTP-MIB::vtpConfigRevNumberError": "1.3.6.1.4.1.9.9.46.2.0.1",
    "CISCO-VTP-MIB::vtpConfigDigestError": "1.3.6.1.4.1.9.9.46.2.0.2",
    "CISCO-VTP-MIB::vtpServerDisabled": "1.3.6.1.4.1.9.9.46.2.0.3",
    "CISCO-VTP-MIB::vtpMtuTooBig": "1.3.6.1.4.1.9.9.46.2.0.4",
    "CISCO-VTP-MIB::vtpVersionOneDeviceDetected": "1.3.6.1.4.1.9.9.46.2.0.6",
    "CISCO-VTP-MIB::vlanTrunkPortDynamicStatusChange": "1.3.6.1.4.1.9.9.46.2.0.7",
    "CISCO-VTP-MIB::vtpLocalModeChanged": "1.3.6.1.4.1.9.9.46.2.0.8",
    "CISCO-VTP-MIB::vtpVersionInUseChanged": "1.3.6.1.4.1.9.9.46.2.0.9",
    "CISCO-VTP-MIB::vtpVlanCreated": "1.3.6.1.4.1.9.9.46.2.0.10",
    "CISCO-VTP-MIB::vtpVlanDeleted": "1.3.6.1.4.1.9.9.46.2.0.11",
    "CISCO-VTP-MIB::vtpVlanRingNumberConflict": "1.3.6.1.4.1.9.9.46.2.0.12",
    "CISCO-VTP-MIB::vtpPruningStateOperChange": "1.3.6.1.4.1.9.9.46.2.0.13",
    "CISCO-VTP-MIB::vtpNotificationsObjects": "1.3.6.1.4.1.9.9.46.2.1",
    "CISCO-VTP-MIB::vtpVlanPortLocalSegment": "1.3.6.1.4.1.9.9.46.2.1.1",
    "CISCO-VTP-MIB::vtpMIBConformance": "1.3.6.1.4.1.9.9.46.3",
    "CISCO-VTP-MIB::vtpMIBCompliances": "1.3.6.1.4.1.9.9.46.3.1",
    "CISCO-VTP-MIB::vtpMIBGroups": "1.3.6.1.4.1.9.9.46.3.2",
}

DISPLAY_HINTS = {
    "1.3.6.1.4.1.9.9.46.1.2.1.1.6": ("OctetString", "2d-1d-1d,1d:1d:1d.1d,1a1d:1d"),  # CISCO-VTP-MIB::managementDomainLastChange
    "1.3.6.1.4.1.9.9.46.1.3.2.2.1.1": ("OctetString", "255t"),  # CISCO-VTP-MIB::vtpInternalVlanOwner
}
