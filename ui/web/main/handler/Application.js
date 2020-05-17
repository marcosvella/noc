//---------------------------------------------------------------------
// main.handler application
//---------------------------------------------------------------------
// Copyright (C) 2007-2020 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.main.handler.Application");

Ext.define("NOC.main.handler.Application", {
    extend: "NOC.core.ModelApplication",
    requires: [
        "NOC.main.handler.Model"
    ],
    model: "NOC.main.handler.Model",
    search: true,
    helpId: "reference-handler",

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
                    text: __("Handler"),
                    dataIndex: "handler",
                    flex: 1
                }
            ],

            fields: [
                {
                    name: "name",
                    xtype: "textfield",
                    fieldLabel: __("Name"),
                    allowBlank: false,
                    uiStyle: "meduim"
                },
                {
                    name: "handler",
                    xtype: "textfield",
                    fieldLabel: __("Handler"),
                    allowBlank: false,
                    vtype: "handler",
                    uiStyle: "medium"
                },
                {
                    name: "description",
                    xtype: "textarea",
                    fieldLabel: __("Description"),
                    allowBlank: true
                },
                {
                    name: "allow_config_filter",
                    xtype: "checkbox",
                    boxLabel: __("Allow Config Filter")
                },
                {
                    name: "allow_config_validation",
                    xtype: "checkbox",
                    boxLabel: __("Allow Config Validation")
                },
                {
                    name: "allow_config_diff",
                    xtype: "checkbox",
                    boxLabel: __("Allow Config Diff")
                },
                {
                    name: "allow_config_diff_filter",
                    xtype: "checkbox",
                    boxLabel: __("Allow Config Diff Filter")
                },
                {
                    name: "allow_housekeeping",
                    xtype: "checkbox",
                    boxLabel: __("Allow housekeeping")
                },
                {
                    name: "allow_resolver",
                    xtype: "checkbox",
                    boxLabel: __("Allow Resolver")
                },
                {
                    name: "allow_threshold",
                    xtype: "checkbox",
                    boxLabel: __("Allow Threshold")
                },
                {
                    name: "allow_ds_filter",
                    xtype: "checkbox",
                    boxLabel: __("Allow DataStream filter")
                }
            ]
        });
        me.callParent();
    }
});
