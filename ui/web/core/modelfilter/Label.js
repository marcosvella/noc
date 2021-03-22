//---------------------------------------------------------------------
// NOC.core.modelfilter.Label
// Label model filter
//---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.core.modelfilter.Label");

Ext.define("NOC.core.modelfilter.Label", {
    extend: "NOC.core.modelfilter.Base",
    require: [
        "NOC.core.LabelField"
    ],

    initComponent: function() {
        var me = this;

        Ext.apply(me, {
            items: [
                {
                    xtype: "labelfield",
                    name: me.name,
                    fieldLabel: me.title,
                    labelAlign: "top",
                    // createNewOnEnter: false,
                    // createNewOnBlur: false,
                    itemId: me.name,
                    width: me.width,
                    listeners: {
                        select: {
                            scope: me,
                            fn: me.onChange
                        },
                        change: {
                            scope: me,
                            fn: me.onChange
                        }
                    }
                }
            ]
        });
        me.callParent();
        me.tags = me.getComponent(me.name);
    },

    getFilter: function() {
        var me = this,
            v = me.tags.getValue(),
            r = {};
        if(v) {
            r[me.name + "__name"] = v;
        }
        return r;
    },

    setFilter: function(filter) {
        var me = this,
            name = me.name + "__name";
        if(name in filter){
            me.tags.setValue(filter[name]);
        }
    }
});
