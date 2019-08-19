//---------------------------------------------------------------------
// Form Field
//---------------------------------------------------------------------
// Copyright (C) 2007-2018 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.core.FormField");

Ext.define("NOC.core.ListFormField", {
    extend: "Ext.form.FieldContainer",
    alias: "widget.listform",
    mixins: {
        field: 'Ext.form.field.Field'
    },
    items: [],
    rows: this.rows || 3,
    timerHandler: undefined,
    initComponent: function() {
        var me = this;

        me.scroll = {x: 0, y: 0};
        // me.rows = me.rows || 3;
        me.fields = Ext.clone(me.items).map(function(item) {
            return Ext.Object.merge(item, {isListForm: true})
        });

        me.addButtonEnd = Ext.create("Ext.button.Button", {
            text: __("Append"),
            glyph: NOC.glyph.plus,
            scope: me,
            handler: Ext.pass(me.onAddRecord, true)
        });

        me.addButton = Ext.create("Ext.button.Button", {
            text: __("Insert"),
            glyph: NOC.glyph.indent,
            scope: me,
            handler: Ext.pass(me.onAddRecord)
        });

        me.deleteButton = Ext.create("Ext.button.Button", {
            text: __("Delete"),
            glyph: NOC.glyph.minus,
            disabled: true,
            scope: me,
            handler: me.onDeleteRecord
        });

        me.cloneButton = Ext.create("Ext.button.Button", {
            text: __("Clone"),
            glyph: NOC.glyph.copy,
            disabled: true,
            scope: me,
            handler: me.onCloneRecord
        });

        me.moveUpButton = Ext.create("Ext.button.Button", {
            text: __("Move Up"),
            glyph: NOC.glyph.caret_up,
            scope: me,
            handler: me.onMoveUp
        });

        me.moveDownButton = Ext.create("Ext.button.Button", {
            text: __("Move Down"),
            glyph: NOC.glyph.caret_down,
            scope: me,
            handler: me.onMoveDown
        });

        me.panel = Ext.create("Ext.form.Panel", {
            scrollable: "vertical",
            dockedItems: [
                {
                    xtype: "toolbar",
                    dock: "top",
                    items: [
                        me.addButton,
                        me.addButtonEnd,
                        me.deleteButton,
                        "-",
                        me.cloneButton,
                        "-",
                        me.moveUpButton,
                        me.moveDownButton
                    ]
                }
            ],
            items: [],
            onScrollEnd: me.onScrollEnd
        });
        Ext.apply(me, {
            items: [
                me.panel
            ]
        });
        me.currentSelection = undefined;
        me.callParent();
    },
    onScrollEnd: function(x, y) {
        var me = this;
        me.scroll = {x: x, y: y};
    },
    getFormData: function(form) {
        var me = this,
            fields = form.getFields().items,
            f, field, data, name,
            fLen = fields.length,
            values = {};
        for(f = 0; f < fLen; f++) {
            field = fields[f];
            data = field.getModelData();
            if(Ext.isObject(data)) {
                name = field.getName();
                if(data.hasOwnProperty(name)) {
                    values[name] = data[name];
                }
            }
        }
        return values;
    },
    getValue: function() {
        var me = this,
            records = [];
        me.panel.items.each(function(panel) {
            records.push(me.getFormData(panel.form))
        });
        return records;
    },
    setValue: function(v) {
        var me = this;
        if(v === undefined || v === "") {
            v = [];
        } else {
            v = v || [];
        }
        if(!Ext.isEmpty(v) && me.timerHandler) {
            clearTimeout(me.timerHandler);
            me.timerHandler = undefined;
        }
        if(me.panel.items.length) {
            me.panel.removeAll();
        }
        Ext.each(v, me.createForm, me);
        me.currentSelection = undefined;
        me.disableButtons(true);
    },
    reset: function() {
        var me = this;
        me.timerHandler = setTimeout(function(scope) {
            scope.removeAll();
        }, 750, me.panel);
    },
    onAddRecord: function() {
        var me = this, index;
        if(Ext.isBoolean(arguments[0]) && arguments[0]) {
            // to end
            index = me.panel.items.length;
        } else {
            index = me.panel.items.findIndexBy(function(i) {
                return i.itemId === me.currentSelection
            }, me) + 1;
        }
        me.createForm(undefined, index);
    },
    onDeleteRecord: function() {
        this.deleteRecord();
    },
    onCloneRecord: function() {
        var me = this;
        me.createForm(me.panel.getComponent(me.currentSelection).getValues());
    },
    onMoveDown: function() {
        var me = this, index, yPosition, yStep;
        index = me.panel.items.findIndexBy(function(i) {
            return i.itemId === me.currentSelection
        }, me);
        if(index < me.panel.items.getCount() - 1) {
            me.panel.moveAfter(me.panel.items.get(index), me.panel.items.get(index + 1));
            yStep = me.panel.getScrollable().getMaxPosition().y / (me.panel.items.length - me.rows);
            yPosition = me.panel.getScrollable().getPosition().y;
            me.panel.getScrollable().scrollTo(null, yPosition + yStep, false);
        }
    },
    onMoveUp: function() {
        var me = this, index, yPosition, yStep;
        index = me.panel.items.findIndexBy(function(i) {
            return i.itemId === me.currentSelection
        }, me);
        if(index > 0) {
            me.panel.moveBefore(me.panel.items.get(index), me.panel.items.get(index - 1));
            if(index > me.rows) {
                yStep = me.panel.getScrollable().getMaxPosition().y / (me.panel.items.length - me.rows);
                yPosition = me.panel.getScrollable().getPosition().y;
                me.panel.getScrollable().scrollTo(null, yPosition - yStep, false);
            }
        }
    },
    createForm: function(record, index) {
        var me = this, formPanel, itemId;
        if(index === undefined) {
            index = me.panel.items.getCount();
        }
        itemId = Ext.id(null, "list-form-");
        formPanel = Ext.create('Ext.form.Panel', {
            itemId: itemId,
            items: me.fields,
            defaults: {
                margin: "5 30 0 10"
            },
            listeners: {
                scope: me,
                focusenter: function(self) {
                    var me = this;
                    // reset selected label
                    me.panel.items.each(function(panel) {
                        panel.setBodyStyle("border-width", "3 3 0 1");
                        panel.setBodyStyle("margin-left", "5px")
                    });
                    me.selected(self);
                    me.currentSelection = self.itemId;
                    me.disableButtons(false);
                },
                afterrender: function(self) {
                    var me = this;
                    me.panel.setMaxHeight((self.getHeight() + 6) * me.rows + 6);
                }
            }
        });
        formPanel.setBodyStyle("border-width", "3 3 0 3");
        formPanel.setBodyStyle("margin-left", "3p   x");
        if(record != null) {
            formPanel.form.setValues(record);
        }
        me.panel.insert(index, formPanel);
        formPanel.items.get(0).focus();
    },
    disableButtons: function(arg) {
        var me = this;
        me.addButton.setDisabled(arg);
        me.deleteButton.setDisabled(arg);
        me.cloneButton.setDisabled(arg);
    },
    selected: function(panel) {
        panel.setBodyStyle("border-width", "3 3 0 6");
        panel.setBodyStyle("margin-left", "0px");
    },
    deleteRecord: function() {
        var me = this;
        // remove by itemId
        me.panel.remove(me.currentSelection);
        me.currentSelection = undefined;
        me.disableButtons(true);
    }
});
