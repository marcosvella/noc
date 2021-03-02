//---------------------------------------------------------------------
// inv.sensorprofile application
//---------------------------------------------------------------------
// Copyright (C) 2007-2020 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.inv.sensorprofile.Application");

Ext.define("NOC.inv.sensorprofile.Application", {
  extend: "NOC.core.ModelApplication",
  requires: [
    "NOC.core.TagsField",
    "NOC.inv.sensorprofile.Model",
    "NOC.wf.workflow.LookupField",
    "NOC.main.style.LookupField"
  ],
  model: "NOC.inv.sensorprofile.Model",
  search: true,
  rowClassField: "row_class",

  initComponent: function() {
    var me = this;
    Ext.apply(me, {
      columns: [
        {
          text: __("Name"),
          dataIndex: "name",
          flex: 1
        },
        {
          text: __("Tags"),
          dataIndex: "tags",
          renderer: NOC.render.Tags,
          width: 100
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
          allowBlank: true,
          uiStyle: "extra"
        },
        {
          name: "workflow",
          xtype: "wf.workflow.LookupField",
          fieldLabel: __("WorkFlow"),
          labelAlign: "left",
          allowBlank: false
        },
        {
          name: "style",
          xtype: "main.style.LookupField",
          fieldLabel: __("Style"),
          labelAlign: "left",
          allowBlank: true
        },
        {
          name: "enable_collect",
          xtype: "checkbox",
          boxLabel: __("Enable Collect"),
          allowBlank: true
        },
        {
          name: "bi_id",
          xtype: "displayfield",
          fieldLabel: __("BI ID"),
          allowBlank: true,
          uiStyle: "medium"
        },
        {
          name: "tags",
          fieldLabel: __("Tags"),
          xtype: "tagsfield",
          allowBlank: true
        }
      ]
    });
    me.callParent();
  }
});
