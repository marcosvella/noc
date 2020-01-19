# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# ADSL-LINE-MIB
# Compiled MIB
# Do not modify this file directly
# Run ./noc mib make-cmib instead
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# MIB Name
NAME = "ADSL-LINE-MIB"

# Metadata
LAST_UPDATED = "1999-08-19"
COMPILED = "2020-01-19"

# MIB Data: name -> oid
MIB = {
    "ADSL-LINE-MIB::adslMIB": "1.3.6.1.2.1.10.94",
    "ADSL-LINE-MIB::adslLineMib": "1.3.6.1.2.1.10.94.1",
    "ADSL-LINE-MIB::adslMibObjects": "1.3.6.1.2.1.10.94.1.1",
    "ADSL-LINE-MIB::adslLineTable": "1.3.6.1.2.1.10.94.1.1.1",
    "ADSL-LINE-MIB::adslLineEntry": "1.3.6.1.2.1.10.94.1.1.1.1",
    "ADSL-LINE-MIB::adslLineCoding": "1.3.6.1.2.1.10.94.1.1.1.1.1",
    "ADSL-LINE-MIB::adslLineType": "1.3.6.1.2.1.10.94.1.1.1.1.2",
    "ADSL-LINE-MIB::adslLineSpecific": "1.3.6.1.2.1.10.94.1.1.1.1.3",
    "ADSL-LINE-MIB::adslLineConfProfile": "1.3.6.1.2.1.10.94.1.1.1.1.4",
    "ADSL-LINE-MIB::adslLineAlarmConfProfile": "1.3.6.1.2.1.10.94.1.1.1.1.5",
    "ADSL-LINE-MIB::adslAtucPhysTable": "1.3.6.1.2.1.10.94.1.1.2",
    "ADSL-LINE-MIB::adslAtucPhysEntry": "1.3.6.1.2.1.10.94.1.1.2.1",
    "ADSL-LINE-MIB::adslAtucInvSerialNumber": "1.3.6.1.2.1.10.94.1.1.2.1.1",
    "ADSL-LINE-MIB::adslAtucInvVendorID": "1.3.6.1.2.1.10.94.1.1.2.1.2",
    "ADSL-LINE-MIB::adslAtucInvVersionNumber": "1.3.6.1.2.1.10.94.1.1.2.1.3",
    "ADSL-LINE-MIB::adslAtucCurrSnrMgn": "1.3.6.1.2.1.10.94.1.1.2.1.4",
    "ADSL-LINE-MIB::adslAtucCurrAtn": "1.3.6.1.2.1.10.94.1.1.2.1.5",
    "ADSL-LINE-MIB::adslAtucCurrStatus": "1.3.6.1.2.1.10.94.1.1.2.1.6",
    "ADSL-LINE-MIB::adslAtucCurrOutputPwr": "1.3.6.1.2.1.10.94.1.1.2.1.7",
    "ADSL-LINE-MIB::adslAtucCurrAttainableRate": "1.3.6.1.2.1.10.94.1.1.2.1.8",
    "ADSL-LINE-MIB::adslAturPhysTable": "1.3.6.1.2.1.10.94.1.1.3",
    "ADSL-LINE-MIB::adslAturPhysEntry": "1.3.6.1.2.1.10.94.1.1.3.1",
    "ADSL-LINE-MIB::adslAturInvSerialNumber": "1.3.6.1.2.1.10.94.1.1.3.1.1",
    "ADSL-LINE-MIB::adslAturInvVendorID": "1.3.6.1.2.1.10.94.1.1.3.1.2",
    "ADSL-LINE-MIB::adslAturInvVersionNumber": "1.3.6.1.2.1.10.94.1.1.3.1.3",
    "ADSL-LINE-MIB::adslAturCurrSnrMgn": "1.3.6.1.2.1.10.94.1.1.3.1.4",
    "ADSL-LINE-MIB::adslAturCurrAtn": "1.3.6.1.2.1.10.94.1.1.3.1.5",
    "ADSL-LINE-MIB::adslAturCurrStatus": "1.3.6.1.2.1.10.94.1.1.3.1.6",
    "ADSL-LINE-MIB::adslAturCurrOutputPwr": "1.3.6.1.2.1.10.94.1.1.3.1.7",
    "ADSL-LINE-MIB::adslAturCurrAttainableRate": "1.3.6.1.2.1.10.94.1.1.3.1.8",
    "ADSL-LINE-MIB::adslAtucChanTable": "1.3.6.1.2.1.10.94.1.1.4",
    "ADSL-LINE-MIB::adslAtucChanEntry": "1.3.6.1.2.1.10.94.1.1.4.1",
    "ADSL-LINE-MIB::adslAtucChanInterleaveDelay": "1.3.6.1.2.1.10.94.1.1.4.1.1",
    "ADSL-LINE-MIB::adslAtucChanCurrTxRate": "1.3.6.1.2.1.10.94.1.1.4.1.2",
    "ADSL-LINE-MIB::adslAtucChanPrevTxRate": "1.3.6.1.2.1.10.94.1.1.4.1.3",
    "ADSL-LINE-MIB::adslAtucChanCrcBlockLength": "1.3.6.1.2.1.10.94.1.1.4.1.4",
    "ADSL-LINE-MIB::adslAturChanTable": "1.3.6.1.2.1.10.94.1.1.5",
    "ADSL-LINE-MIB::adslAturChanEntry": "1.3.6.1.2.1.10.94.1.1.5.1",
    "ADSL-LINE-MIB::adslAturChanInterleaveDelay": "1.3.6.1.2.1.10.94.1.1.5.1.1",
    "ADSL-LINE-MIB::adslAturChanCurrTxRate": "1.3.6.1.2.1.10.94.1.1.5.1.2",
    "ADSL-LINE-MIB::adslAturChanPrevTxRate": "1.3.6.1.2.1.10.94.1.1.5.1.3",
    "ADSL-LINE-MIB::adslAturChanCrcBlockLength": "1.3.6.1.2.1.10.94.1.1.5.1.4",
    "ADSL-LINE-MIB::adslAtucPerfDataTable": "1.3.6.1.2.1.10.94.1.1.6",
    "ADSL-LINE-MIB::adslAtucPerfDataEntry": "1.3.6.1.2.1.10.94.1.1.6.1",
    "ADSL-LINE-MIB::adslAtucPerfLofs": "1.3.6.1.2.1.10.94.1.1.6.1.1",
    "ADSL-LINE-MIB::adslAtucPerfLoss": "1.3.6.1.2.1.10.94.1.1.6.1.2",
    "ADSL-LINE-MIB::adslAtucPerfLols": "1.3.6.1.2.1.10.94.1.1.6.1.3",
    "ADSL-LINE-MIB::adslAtucPerfLprs": "1.3.6.1.2.1.10.94.1.1.6.1.4",
    "ADSL-LINE-MIB::adslAtucPerfESs": "1.3.6.1.2.1.10.94.1.1.6.1.5",
    "ADSL-LINE-MIB::adslAtucPerfInits": "1.3.6.1.2.1.10.94.1.1.6.1.6",
    "ADSL-LINE-MIB::adslAtucPerfValidIntervals": "1.3.6.1.2.1.10.94.1.1.6.1.7",
    "ADSL-LINE-MIB::adslAtucPerfInvalidIntervals": "1.3.6.1.2.1.10.94.1.1.6.1.8",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinTimeElapsed": "1.3.6.1.2.1.10.94.1.1.6.1.9",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinLofs": "1.3.6.1.2.1.10.94.1.1.6.1.10",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinLoss": "1.3.6.1.2.1.10.94.1.1.6.1.11",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinLols": "1.3.6.1.2.1.10.94.1.1.6.1.12",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinLprs": "1.3.6.1.2.1.10.94.1.1.6.1.13",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinESs": "1.3.6.1.2.1.10.94.1.1.6.1.14",
    "ADSL-LINE-MIB::adslAtucPerfCurr15MinInits": "1.3.6.1.2.1.10.94.1.1.6.1.15",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayTimeElapsed": "1.3.6.1.2.1.10.94.1.1.6.1.16",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayLofs": "1.3.6.1.2.1.10.94.1.1.6.1.17",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayLoss": "1.3.6.1.2.1.10.94.1.1.6.1.18",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayLols": "1.3.6.1.2.1.10.94.1.1.6.1.19",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayLprs": "1.3.6.1.2.1.10.94.1.1.6.1.20",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayESs": "1.3.6.1.2.1.10.94.1.1.6.1.21",
    "ADSL-LINE-MIB::adslAtucPerfCurr1DayInits": "1.3.6.1.2.1.10.94.1.1.6.1.22",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayMoniSecs": "1.3.6.1.2.1.10.94.1.1.6.1.23",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayLofs": "1.3.6.1.2.1.10.94.1.1.6.1.24",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayLoss": "1.3.6.1.2.1.10.94.1.1.6.1.25",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayLols": "1.3.6.1.2.1.10.94.1.1.6.1.26",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayLprs": "1.3.6.1.2.1.10.94.1.1.6.1.27",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayESs": "1.3.6.1.2.1.10.94.1.1.6.1.28",
    "ADSL-LINE-MIB::adslAtucPerfPrev1DayInits": "1.3.6.1.2.1.10.94.1.1.6.1.29",
    "ADSL-LINE-MIB::adslAturPerfDataTable": "1.3.6.1.2.1.10.94.1.1.7",
    "ADSL-LINE-MIB::adslAturPerfDataEntry": "1.3.6.1.2.1.10.94.1.1.7.1",
    "ADSL-LINE-MIB::adslAturPerfLofs": "1.3.6.1.2.1.10.94.1.1.7.1.1",
    "ADSL-LINE-MIB::adslAturPerfLoss": "1.3.6.1.2.1.10.94.1.1.7.1.2",
    "ADSL-LINE-MIB::adslAturPerfLprs": "1.3.6.1.2.1.10.94.1.1.7.1.3",
    "ADSL-LINE-MIB::adslAturPerfESs": "1.3.6.1.2.1.10.94.1.1.7.1.4",
    "ADSL-LINE-MIB::adslAturPerfValidIntervals": "1.3.6.1.2.1.10.94.1.1.7.1.5",
    "ADSL-LINE-MIB::adslAturPerfInvalidIntervals": "1.3.6.1.2.1.10.94.1.1.7.1.6",
    "ADSL-LINE-MIB::adslAturPerfCurr15MinTimeElapsed": "1.3.6.1.2.1.10.94.1.1.7.1.7",
    "ADSL-LINE-MIB::adslAturPerfCurr15MinLofs": "1.3.6.1.2.1.10.94.1.1.7.1.8",
    "ADSL-LINE-MIB::adslAturPerfCurr15MinLoss": "1.3.6.1.2.1.10.94.1.1.7.1.9",
    "ADSL-LINE-MIB::adslAturPerfCurr15MinLprs": "1.3.6.1.2.1.10.94.1.1.7.1.10",
    "ADSL-LINE-MIB::adslAturPerfCurr15MinESs": "1.3.6.1.2.1.10.94.1.1.7.1.11",
    "ADSL-LINE-MIB::adslAturPerfCurr1DayTimeElapsed": "1.3.6.1.2.1.10.94.1.1.7.1.12",
    "ADSL-LINE-MIB::adslAturPerfCurr1DayLofs": "1.3.6.1.2.1.10.94.1.1.7.1.13",
    "ADSL-LINE-MIB::adslAturPerfCurr1DayLoss": "1.3.6.1.2.1.10.94.1.1.7.1.14",
    "ADSL-LINE-MIB::adslAturPerfCurr1DayLprs": "1.3.6.1.2.1.10.94.1.1.7.1.15",
    "ADSL-LINE-MIB::adslAturPerfCurr1DayESs": "1.3.6.1.2.1.10.94.1.1.7.1.16",
    "ADSL-LINE-MIB::adslAturPerfPrev1DayMoniSecs": "1.3.6.1.2.1.10.94.1.1.7.1.17",
    "ADSL-LINE-MIB::adslAturPerfPrev1DayLofs": "1.3.6.1.2.1.10.94.1.1.7.1.18",
    "ADSL-LINE-MIB::adslAturPerfPrev1DayLoss": "1.3.6.1.2.1.10.94.1.1.7.1.19",
    "ADSL-LINE-MIB::adslAturPerfPrev1DayLprs": "1.3.6.1.2.1.10.94.1.1.7.1.20",
    "ADSL-LINE-MIB::adslAturPerfPrev1DayESs": "1.3.6.1.2.1.10.94.1.1.7.1.21",
    "ADSL-LINE-MIB::adslAtucIntervalTable": "1.3.6.1.2.1.10.94.1.1.8",
    "ADSL-LINE-MIB::adslAtucIntervalEntry": "1.3.6.1.2.1.10.94.1.1.8.1",
    "ADSL-LINE-MIB::adslAtucIntervalNumber": "1.3.6.1.2.1.10.94.1.1.8.1.1",
    "ADSL-LINE-MIB::adslAtucIntervalLofs": "1.3.6.1.2.1.10.94.1.1.8.1.2",
    "ADSL-LINE-MIB::adslAtucIntervalLoss": "1.3.6.1.2.1.10.94.1.1.8.1.3",
    "ADSL-LINE-MIB::adslAtucIntervalLols": "1.3.6.1.2.1.10.94.1.1.8.1.4",
    "ADSL-LINE-MIB::adslAtucIntervalLprs": "1.3.6.1.2.1.10.94.1.1.8.1.5",
    "ADSL-LINE-MIB::adslAtucIntervalESs": "1.3.6.1.2.1.10.94.1.1.8.1.6",
    "ADSL-LINE-MIB::adslAtucIntervalInits": "1.3.6.1.2.1.10.94.1.1.8.1.7",
    "ADSL-LINE-MIB::adslAtucIntervalValidData": "1.3.6.1.2.1.10.94.1.1.8.1.8",
    "ADSL-LINE-MIB::adslAturIntervalTable": "1.3.6.1.2.1.10.94.1.1.9",
    "ADSL-LINE-MIB::adslAturIntervalEntry": "1.3.6.1.2.1.10.94.1.1.9.1",
    "ADSL-LINE-MIB::adslAturIntervalNumber": "1.3.6.1.2.1.10.94.1.1.9.1.1",
    "ADSL-LINE-MIB::adslAturIntervalLofs": "1.3.6.1.2.1.10.94.1.1.9.1.2",
    "ADSL-LINE-MIB::adslAturIntervalLoss": "1.3.6.1.2.1.10.94.1.1.9.1.3",
    "ADSL-LINE-MIB::adslAturIntervalLprs": "1.3.6.1.2.1.10.94.1.1.9.1.4",
    "ADSL-LINE-MIB::adslAturIntervalESs": "1.3.6.1.2.1.10.94.1.1.9.1.5",
    "ADSL-LINE-MIB::adslAturIntervalValidData": "1.3.6.1.2.1.10.94.1.1.9.1.6",
    "ADSL-LINE-MIB::adslAtucChanPerfDataTable": "1.3.6.1.2.1.10.94.1.1.10",
    "ADSL-LINE-MIB::adslAtucChanPerfDataEntry": "1.3.6.1.2.1.10.94.1.1.10.1",
    "ADSL-LINE-MIB::adslAtucChanReceivedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.1",
    "ADSL-LINE-MIB::adslAtucChanTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.2",
    "ADSL-LINE-MIB::adslAtucChanCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.3",
    "ADSL-LINE-MIB::adslAtucChanUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.10.1.4",
    "ADSL-LINE-MIB::adslAtucChanPerfValidIntervals": "1.3.6.1.2.1.10.94.1.1.10.1.5",
    "ADSL-LINE-MIB::adslAtucChanPerfInvalidIntervals": "1.3.6.1.2.1.10.94.1.1.10.1.6",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr15MinTimeElapsed": "1.3.6.1.2.1.10.94.1.1.10.1.7",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr15MinReceivedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.8",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr15MinTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.9",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr15MinCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.10",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr15MinUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.10.1.11",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr1DayTimeElapsed": "1.3.6.1.2.1.10.94.1.1.10.1.12",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr1DayReceivedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.13",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr1DayTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.14",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr1DayCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.15",
    "ADSL-LINE-MIB::adslAtucChanPerfCurr1DayUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.10.1.16",
    "ADSL-LINE-MIB::adslAtucChanPerfPrev1DayMoniSecs": "1.3.6.1.2.1.10.94.1.1.10.1.17",
    "ADSL-LINE-MIB::adslAtucChanPerfPrev1DayReceivedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.18",
    "ADSL-LINE-MIB::adslAtucChanPerfPrev1DayTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.19",
    "ADSL-LINE-MIB::adslAtucChanPerfPrev1DayCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.10.1.20",
    "ADSL-LINE-MIB::adslAtucChanPerfPrev1DayUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.10.1.21",
    "ADSL-LINE-MIB::adslAturChanPerfDataTable": "1.3.6.1.2.1.10.94.1.1.11",
    "ADSL-LINE-MIB::adslAturChanPerfDataEntry": "1.3.6.1.2.1.10.94.1.1.11.1",
    "ADSL-LINE-MIB::adslAturChanReceivedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.1",
    "ADSL-LINE-MIB::adslAturChanTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.2",
    "ADSL-LINE-MIB::adslAturChanCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.3",
    "ADSL-LINE-MIB::adslAturChanUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.11.1.4",
    "ADSL-LINE-MIB::adslAturChanPerfValidIntervals": "1.3.6.1.2.1.10.94.1.1.11.1.5",
    "ADSL-LINE-MIB::adslAturChanPerfInvalidIntervals": "1.3.6.1.2.1.10.94.1.1.11.1.6",
    "ADSL-LINE-MIB::adslAturChanPerfCurr15MinTimeElapsed": "1.3.6.1.2.1.10.94.1.1.11.1.7",
    "ADSL-LINE-MIB::adslAturChanPerfCurr15MinReceivedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.8",
    "ADSL-LINE-MIB::adslAturChanPerfCurr15MinTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.9",
    "ADSL-LINE-MIB::adslAturChanPerfCurr15MinCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.10",
    "ADSL-LINE-MIB::adslAturChanPerfCurr15MinUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.11.1.11",
    "ADSL-LINE-MIB::adslAturChanPerfCurr1DayTimeElapsed": "1.3.6.1.2.1.10.94.1.1.11.1.12",
    "ADSL-LINE-MIB::adslAturChanPerfCurr1DayReceivedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.13",
    "ADSL-LINE-MIB::adslAturChanPerfCurr1DayTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.14",
    "ADSL-LINE-MIB::adslAturChanPerfCurr1DayCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.15",
    "ADSL-LINE-MIB::adslAturChanPerfCurr1DayUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.11.1.16",
    "ADSL-LINE-MIB::adslAturChanPerfPrev1DayMoniSecs": "1.3.6.1.2.1.10.94.1.1.11.1.17",
    "ADSL-LINE-MIB::adslAturChanPerfPrev1DayReceivedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.18",
    "ADSL-LINE-MIB::adslAturChanPerfPrev1DayTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.19",
    "ADSL-LINE-MIB::adslAturChanPerfPrev1DayCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.11.1.20",
    "ADSL-LINE-MIB::adslAturChanPerfPrev1DayUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.11.1.21",
    "ADSL-LINE-MIB::adslAtucChanIntervalTable": "1.3.6.1.2.1.10.94.1.1.12",
    "ADSL-LINE-MIB::adslAtucChanIntervalEntry": "1.3.6.1.2.1.10.94.1.1.12.1",
    "ADSL-LINE-MIB::adslAtucChanIntervalNumber": "1.3.6.1.2.1.10.94.1.1.12.1.1",
    "ADSL-LINE-MIB::adslAtucChanIntervalReceivedBlks": "1.3.6.1.2.1.10.94.1.1.12.1.2",
    "ADSL-LINE-MIB::adslAtucChanIntervalTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.12.1.3",
    "ADSL-LINE-MIB::adslAtucChanIntervalCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.12.1.4",
    "ADSL-LINE-MIB::adslAtucChanIntervalUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.12.1.5",
    "ADSL-LINE-MIB::adslAtucChanIntervalValidData": "1.3.6.1.2.1.10.94.1.1.12.1.6",
    "ADSL-LINE-MIB::adslAturChanIntervalTable": "1.3.6.1.2.1.10.94.1.1.13",
    "ADSL-LINE-MIB::adslAturChanIntervalEntry": "1.3.6.1.2.1.10.94.1.1.13.1",
    "ADSL-LINE-MIB::adslAturChanIntervalNumber": "1.3.6.1.2.1.10.94.1.1.13.1.1",
    "ADSL-LINE-MIB::adslAturChanIntervalReceivedBlks": "1.3.6.1.2.1.10.94.1.1.13.1.2",
    "ADSL-LINE-MIB::adslAturChanIntervalTransmittedBlks": "1.3.6.1.2.1.10.94.1.1.13.1.3",
    "ADSL-LINE-MIB::adslAturChanIntervalCorrectedBlks": "1.3.6.1.2.1.10.94.1.1.13.1.4",
    "ADSL-LINE-MIB::adslAturChanIntervalUncorrectBlks": "1.3.6.1.2.1.10.94.1.1.13.1.5",
    "ADSL-LINE-MIB::adslAturChanIntervalValidData": "1.3.6.1.2.1.10.94.1.1.13.1.6",
    "ADSL-LINE-MIB::adslLineConfProfileTable": "1.3.6.1.2.1.10.94.1.1.14",
    "ADSL-LINE-MIB::adslLineConfProfileEntry": "1.3.6.1.2.1.10.94.1.1.14.1",
    "ADSL-LINE-MIB::adslLineConfProfileName": "1.3.6.1.2.1.10.94.1.1.14.1.1",
    "ADSL-LINE-MIB::adslAtucConfRateMode": "1.3.6.1.2.1.10.94.1.1.14.1.2",
    "ADSL-LINE-MIB::adslAtucConfRateChanRatio": "1.3.6.1.2.1.10.94.1.1.14.1.3",
    "ADSL-LINE-MIB::adslAtucConfTargetSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.4",
    "ADSL-LINE-MIB::adslAtucConfMaxSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.5",
    "ADSL-LINE-MIB::adslAtucConfMinSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.6",
    "ADSL-LINE-MIB::adslAtucConfDownshiftSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.7",
    "ADSL-LINE-MIB::adslAtucConfUpshiftSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.8",
    "ADSL-LINE-MIB::adslAtucConfMinUpshiftTime": "1.3.6.1.2.1.10.94.1.1.14.1.9",
    "ADSL-LINE-MIB::adslAtucConfMinDownshiftTime": "1.3.6.1.2.1.10.94.1.1.14.1.10",
    "ADSL-LINE-MIB::adslAtucChanConfFastMinTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.11",
    "ADSL-LINE-MIB::adslAtucChanConfInterleaveMinTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.12",
    "ADSL-LINE-MIB::adslAtucChanConfFastMaxTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.13",
    "ADSL-LINE-MIB::adslAtucChanConfInterleaveMaxTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.14",
    "ADSL-LINE-MIB::adslAtucChanConfMaxInterleaveDelay": "1.3.6.1.2.1.10.94.1.1.14.1.15",
    "ADSL-LINE-MIB::adslAturConfRateMode": "1.3.6.1.2.1.10.94.1.1.14.1.16",
    "ADSL-LINE-MIB::adslAturConfRateChanRatio": "1.3.6.1.2.1.10.94.1.1.14.1.17",
    "ADSL-LINE-MIB::adslAturConfTargetSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.18",
    "ADSL-LINE-MIB::adslAturConfMaxSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.19",
    "ADSL-LINE-MIB::adslAturConfMinSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.20",
    "ADSL-LINE-MIB::adslAturConfDownshiftSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.21",
    "ADSL-LINE-MIB::adslAturConfUpshiftSnrMgn": "1.3.6.1.2.1.10.94.1.1.14.1.22",
    "ADSL-LINE-MIB::adslAturConfMinUpshiftTime": "1.3.6.1.2.1.10.94.1.1.14.1.23",
    "ADSL-LINE-MIB::adslAturConfMinDownshiftTime": "1.3.6.1.2.1.10.94.1.1.14.1.24",
    "ADSL-LINE-MIB::adslAturChanConfFastMinTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.25",
    "ADSL-LINE-MIB::adslAturChanConfInterleaveMinTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.26",
    "ADSL-LINE-MIB::adslAturChanConfFastMaxTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.27",
    "ADSL-LINE-MIB::adslAturChanConfInterleaveMaxTxRate": "1.3.6.1.2.1.10.94.1.1.14.1.28",
    "ADSL-LINE-MIB::adslAturChanConfMaxInterleaveDelay": "1.3.6.1.2.1.10.94.1.1.14.1.29",
    "ADSL-LINE-MIB::adslLineConfProfileRowStatus": "1.3.6.1.2.1.10.94.1.1.14.1.30",
    "ADSL-LINE-MIB::adslLineAlarmConfProfileTable": "1.3.6.1.2.1.10.94.1.1.15",
    "ADSL-LINE-MIB::adslLineAlarmConfProfileEntry": "1.3.6.1.2.1.10.94.1.1.15.1",
    "ADSL-LINE-MIB::adslLineAlarmConfProfileName": "1.3.6.1.2.1.10.94.1.1.15.1.1",
    "ADSL-LINE-MIB::adslAtucThresh15MinLofs": "1.3.6.1.2.1.10.94.1.1.15.1.2",
    "ADSL-LINE-MIB::adslAtucThresh15MinLoss": "1.3.6.1.2.1.10.94.1.1.15.1.3",
    "ADSL-LINE-MIB::adslAtucThresh15MinLols": "1.3.6.1.2.1.10.94.1.1.15.1.4",
    "ADSL-LINE-MIB::adslAtucThresh15MinLprs": "1.3.6.1.2.1.10.94.1.1.15.1.5",
    "ADSL-LINE-MIB::adslAtucThresh15MinESs": "1.3.6.1.2.1.10.94.1.1.15.1.6",
    "ADSL-LINE-MIB::adslAtucThreshFastRateUp": "1.3.6.1.2.1.10.94.1.1.15.1.7",
    "ADSL-LINE-MIB::adslAtucThreshInterleaveRateUp": "1.3.6.1.2.1.10.94.1.1.15.1.8",
    "ADSL-LINE-MIB::adslAtucThreshFastRateDown": "1.3.6.1.2.1.10.94.1.1.15.1.9",
    "ADSL-LINE-MIB::adslAtucThreshInterleaveRateDown": "1.3.6.1.2.1.10.94.1.1.15.1.10",
    "ADSL-LINE-MIB::adslAtucInitFailureTrapEnable": "1.3.6.1.2.1.10.94.1.1.15.1.11",
    "ADSL-LINE-MIB::adslAturThresh15MinLofs": "1.3.6.1.2.1.10.94.1.1.15.1.12",
    "ADSL-LINE-MIB::adslAturThresh15MinLoss": "1.3.6.1.2.1.10.94.1.1.15.1.13",
    "ADSL-LINE-MIB::adslAturThresh15MinLprs": "1.3.6.1.2.1.10.94.1.1.15.1.14",
    "ADSL-LINE-MIB::adslAturThresh15MinESs": "1.3.6.1.2.1.10.94.1.1.15.1.15",
    "ADSL-LINE-MIB::adslAturThreshFastRateUp": "1.3.6.1.2.1.10.94.1.1.15.1.16",
    "ADSL-LINE-MIB::adslAturThreshInterleaveRateUp": "1.3.6.1.2.1.10.94.1.1.15.1.17",
    "ADSL-LINE-MIB::adslAturThreshFastRateDown": "1.3.6.1.2.1.10.94.1.1.15.1.18",
    "ADSL-LINE-MIB::adslAturThreshInterleaveRateDown": "1.3.6.1.2.1.10.94.1.1.15.1.19",
    "ADSL-LINE-MIB::adslLineAlarmConfProfileRowStatus": "1.3.6.1.2.1.10.94.1.1.15.1.20",
    "ADSL-LINE-MIB::adslLCSMib": "1.3.6.1.2.1.10.94.1.1.16",
    "ADSL-LINE-MIB::adslTraps": "1.3.6.1.2.1.10.94.1.2",
    "ADSL-LINE-MIB::adslAtucTraps": "1.3.6.1.2.1.10.94.1.2.1",
    "ADSL-LINE-MIB::adslAtucPerfLofsThreshTrap": "1.3.6.1.2.1.10.94.1.2.1.0.1",
    "ADSL-LINE-MIB::adslAtucPerfLossThreshTrap": "1.3.6.1.2.1.10.94.1.2.1.0.2",
    "ADSL-LINE-MIB::adslAtucPerfLprsThreshTrap": "1.3.6.1.2.1.10.94.1.2.1.0.3",
    "ADSL-LINE-MIB::adslAtucPerfESsThreshTrap": "1.3.6.1.2.1.10.94.1.2.1.0.4",
    "ADSL-LINE-MIB::adslAtucRateChangeTrap": "1.3.6.1.2.1.10.94.1.2.1.0.5",
    "ADSL-LINE-MIB::adslAtucPerfLolsThreshTrap": "1.3.6.1.2.1.10.94.1.2.1.0.6",
    "ADSL-LINE-MIB::adslAtucInitFailureTrap": "1.3.6.1.2.1.10.94.1.2.1.0.7",
    "ADSL-LINE-MIB::adslAturTraps": "1.3.6.1.2.1.10.94.1.2.2",
    "ADSL-LINE-MIB::adslAturPerfLofsThreshTrap": "1.3.6.1.2.1.10.94.1.2.2.0.1",
    "ADSL-LINE-MIB::adslAturPerfLossThreshTrap": "1.3.6.1.2.1.10.94.1.2.2.0.2",
    "ADSL-LINE-MIB::adslAturPerfLprsThreshTrap": "1.3.6.1.2.1.10.94.1.2.2.0.3",
    "ADSL-LINE-MIB::adslAturPerfESsThreshTrap": "1.3.6.1.2.1.10.94.1.2.2.0.4",
    "ADSL-LINE-MIB::adslAturRateChangeTrap": "1.3.6.1.2.1.10.94.1.2.2.0.5",
    "ADSL-LINE-MIB::adslConformance": "1.3.6.1.2.1.10.94.1.3",
    "ADSL-LINE-MIB::adslGroups": "1.3.6.1.2.1.10.94.1.3.1",
    "ADSL-LINE-MIB::adslCompliances": "1.3.6.1.2.1.10.94.1.3.2",
}

DISPLAY_HINTS = {

}
