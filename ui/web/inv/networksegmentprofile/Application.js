//---------------------------------------------------------------------
// inv.networksegmentprofile application
//---------------------------------------------------------------------
// Copyright (C) 2007-2018 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.inv.networksegmentprofile.Application");

Ext.define("NOC.inv.networksegmentprofile.Application", {
    extend: "NOC.core.ModelApplication",
    requires: [
        "NOC.inv.networksegmentprofile.Model",
        "NOC.inv.networksegmentprofile.LookupField",
        "NOC.main.style.LookupField",
        "NOC.vc.vlanprofile.LookupField",
        "Ext.ux.form.GridField"
    ],
    model: "NOC.inv.networksegmentprofile.Model",
    search: true,
    helpId: "reference-network-segment-profile",
    rowClassField: "row_class",

    initComponent: function() {
        var me = this;
        Ext.apply(me, {
            columns: [
                {
                    text: __("Name"),
                    dataIndex: "name",
                    width: 150
                },
                {
                    text: __("VLAN Discovery"),
                    dataIndex: "enable_vlan",
                    width: 50,
                    renderer: NOC.render.Bool
                },
                {
                    text: __("Style"),
                    dataIndex: "style",
                    renderer: NOC.render.Lookup("style"),
                    flex: 1
                }
            ],

            fields: [
                {
                    name: "name",
                    xtype: "textfield",
                    fieldLabel: __("Name"),
                    allowBlank: false,
                    uiStyle: "medium"
                },
                {
                    name: "description",
                    xtype: "textarea",
                    fieldLabel: __("Description"),
                    allowBlank: true
                },
                {
                    name: "style",
                    xtype: "main.style.LookupField",
                    fieldLabel: __("Style"),
                    allowBlank: true
                },
                {
                    name: "discovery_interval",
                    xtype: "numberfield",
                    fieldLabel: __("Discovery interval"),
                    allowBlank: false,
                    uiStyle: "small"
                },
                {
                    name: "autocreated_profile",
                    xtype: "inv.networksegmentprofile.LookupField",
                    fieldLabel: __("Autocreated Profile"),
                    allowBlank: true
                },
                {
                    name: "mac_restrict_to_management_vlan",
                    xtype: "checkbox",
                    boxLabel: __("Restrict MAC to management vlan"),
                    allowBlank: true
                },
                {
                    name: "management_vlan",
                    xtype: "numberfield",
                    fieldLabel: __("Management VLAN"),
                    allowBlank: true,
                    uiStyle: "medium",
                    emptyText: __("Not Configured"),
                    submitEmptyText: false,
                    minValue: 1,
                    maxValue: 4095
                },
                {
                    name: "multicast_vlan",
                    xtype: "numberfield",
                    fieldLabel: __("Multicast VLAN"),
                    allowBlank: true,
                    uiStyle: "medium",
                    emptyText: __("Not Configured"),
                    submitEmptyText: false,
                    minValue: 1,
                    maxValue: 4095
                },
                {
                    name: "enable_lost_redundancy",
                    xtype: "checkbox",
                    boxLabel: __("Enable lost redundancy check")
                },
                {
                    name: "horizontal_transit_policy",
                    xtype: "combobox",
                    fieldLabel: __("Horizontal Transit Policy"),
                    allowBlank: false,
                    store: [
                        ["E", __("Always Enable")],
                        ["C", __("Calculate")],
                        ["D", __("Disable")]
                    ],
                    uiStyle: "medium"
                },
                {
                    name: "topology_methods",
                    xtype: "gridfield",
                    fieldLabel: __("Topology methods"),
                    columns: [
                        {
                            text: __("Method"),
                            dataIndex: "method",
                            width: 100,
                            editor: {
                                xtype: "combobox",
                                store: [
                                    ["custom", "Custom ..."],
                                    ["handler", "Handler ..."],
                                    ["cdp", "CDP"],
                                    ["huawei_ndp", "Huawei NDP"],
                                    ["lacp", "LACP"],
                                    ["lldp", "LLDP"],
                                    ["oam", "OAM"],
                                    ["rep", "REP"],
                                    ["stp", "STP"],
                                    ["udld", "UDLD"],
                                    ["fdp", "FDP"],
                                    ["bfd", "BFD"],
                                    ["mac", "MAC"],
                                    ["xmac", "xMAC"],
                                    ["nri", "NRI"],
                                    ["ifdesc", "Iface Description"]
                                ]
                            }
                        },
                        {
                            text: __("Active"),
                            dataIndex: "is_active",
                            editor: "checkbox",
                            renderer: NOC.render.Bool,
                            flex: 1
                        }
                    ]
                },
                {
                    name: "uplink_policy",
                    xtype: "gridfield",
                    fieldLabel: __("Uplink Policy"),
                    columns: [
                        {
                            text: __("Method"),
                            dataIndex: "method",
                            width: 150,
                            editor: {
                                xtype: "combobox",
                                store: [
                                    ["seghier", _("Segment Hierarchy")],
                                    ["molevel", _("Managed Object Level")],
                                    ["seg", _("All Segment Objects")],
                                    ["minaddr", _("Lesser Management Address")],
                                    ["maxaddr", _("Greater Management Address")]
                                ]
                            }
                        },
                        {
                            text: __("Active"),
                            dataIndex: "is_active",
                            editor: "checkbox",
                            renderer: NOC.render.Bool,
                            flex: 1
                        }
                    ]
                },
                {
                    name: "enable_vlan",
                    xtype: "checkbox",
                    boxLabel: __("Enable VLAN Discovery")
                },
                {
                    name: "default_vlan_profile",
                    xtype: "vc.vlanprofile.LookupField",
                    fieldLabel: __("Default VLAN Profile"),
                    allowBlank: true
                },
                {
                    xtype: "fieldset",
                    title: __("Biosegmentation"),
                    items: [
                        {
                            name: "is_persistent",
                            xtype: "checkbox",
                            boxLabel: __("Persistent")
                        },
                        {
                            name: "bio_collision_policy",
                            xtype: "gridfield",
                            fieldLabel: __("Collision Policy"),
                            columns: [
                                {
                                    text: __("Match Type"),
                                    dataIndex: "match_type",
                                    width: 100,
                                    editor: {
                                        xtype: "combobox",
                                        store: [
                                            ["p", __("Persistent")],
                                            ["f", __("Floating")],
                                            ["*", __("Any")]
                                        ]
                                    },
                                    renderer: NOC.render.Choices({
                                        "p": __("Persistent"),
                                        "f": __("Floating"),
                                        "*": __("Any")
                                    })
                                },
                                {
                                    text: __("Match Level"),
                                    dataIndex: "match_level",
                                    width: 100,
                                    editor: {
                                        xtype: "combobox",
                                        store: [
                                            ["-", __("No link")],
                                            ["<", "<"],
                                            ["<=", "<="],
                                            ["==", "=="],
                                            [">=", ">="],
                                            [">", ">"],
                                            ["*", __("Any")]
                                        ]
                                    },
                                    renderer: NOC.render.Choices({
                                        "-": __("No link"),
                                        "<": "<",
                                        "<=": "<=",
                                        "==": "==",
                                        ">=": ">=",
                                        ">": ">",
                                        "*": __("Any")
                                    })
                                },
                                {
                                    text: __("Policy"),
                                    dataIndex: "policy",
                                    flex: 1,
                                    editor: {
                                        xtype: "combobox",
                                        store: [
                                            ["merge", __("Merge")],
                                            ["keep", __("Keep")],
                                            ["eat", __("Eat")],
                                            ["feed", __("Feed")],
                                            ["calcify", __("Calcify")]
                                        ]
                                    },
                                    renderer: NOC.render.Choices({
                                        "merge": __("Merge"),
                                        "keep": __("Keep"),
                                        "eat": __("Eat"),
                                        "feed": __("Feed"),
                                        "calcify": __("Calcify")
                                    })
                                }
                            ]
                        },
                        {
                            name: "calcified_profile",
                            xtype: "inv.networksegmentprofile.LookupField",
                            fieldLabel: __("Calcified Profile"),
                            allowBlank: true
                        }
                    ]
                }
            ]
        });
        me.callParent();
    }
});
