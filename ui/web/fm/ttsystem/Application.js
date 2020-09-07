//---------------------------------------------------------------------
// fm.ttsystem application
//---------------------------------------------------------------------
// Copyright (C) 2007-2016 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.fm.ttsystem.Application");

Ext.define("NOC.fm.ttsystem.Application", {
    extend: "NOC.core.ModelApplication",
    requires: [
        "NOC.fm.ttsystem.Model"
    ],
    model: "NOC.fm.ttsystem.Model",
    initComponent: function() {
        var me = this;
        Ext.apply(me, {
            columns: [
                {
                    text: __("Name"),
                    dataIndex: "name",
                    width: 100
                },
                {
                    text: __("Active"),
                    dataIndex: "is_active",
                    width: 50,
                    renderer: NOC.render.Bool
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
                    allowBlank: false
                },
                {
                    name: "is_active",
                    xtype: "checkbox",
                    fieldLabel: __("Active"),
                    allowBlank: false
                },
                {
                    name: "handler",
                    xtype: "textfield",
                    fieldLabel: __("Handler"),
                    allowBlank: false
                },
                {
                    name: "description",
                    xtype: "textarea",
                    fieldLabel: __("Description"),
                    allowBlank: true
                },
                {
                    name: "connection",
                    xtype: "textfield",
                    fieldLabel: __("Connection"),
                    allowBlank: false
                },
                {
                    name: "shard_name",
                    xtype: "textfield",
                    fieldLabel: __("Shard"),
                    regex: /^[0-9a-zA-z]{1,16}$/,
                    allowBlank: false,
                    uiStyle: "medium"
                },
                {
                    name: "max_threads",
                    xtype: "numberfield",
                    fieldLabel: __("Max. Threads"),
                    allowBlank: false,
                    min: 0,
                    uiStyle: "small"
                },
                {
                    name: "failure_cooldown",
                    xtype: "numberfield",
                    fieldLabel: __("Failure Cooldown"),
                    allowBlank: true,
                    min: 0,
                    uiStyle: "small"
                },
                {
                    text: __("Escalate Alarm Consequence Policy"),
                    dataIndex: "alarm_consequence_policy",
                    renderer: function (value) {
                        return {
                            "D": "Disable",
                            "a": "Escalate with alarm timestamp",
                            "c": "Escalate with current timestamp"
                        }[value];
                    }
                },
                {
                    name: "telemetry_sample",
                    xtype: "numberfield",
                    fieldLabel: __("Tememetry Sample"),
                    allowBlank: false,
                    min: 0,
                    uiStyle: "small"
                }
            ]
        });
        me.callParent();
    }
});
