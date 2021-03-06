//---------------------------------------------------------------------
// NOC.core.LabelField -
// Label Field
//---------------------------------------------------------------------
// Copyright (C) 2007-2021 The NOC Project
// See LICENSE for details
//---------------------------------------------------------------------
console.debug("Defining NOC.core.LabelField");

Ext.define("NOC.core.LabelField", {
    extend: "Ext.form.field.Tag",
    requires: [
        "Ext.selection.Model",
        "Ext.data.Store",
        "Ext.data.ChainedStore",
        "NOC.core.LabelFieldModel"
    ],
    alias: "widget.labelfield",
    displayField: "name",
    valueField: "id",
    queryParam: "__query",
    queryMode: "remote",
    autoLoadOnValue: true,
    filterPickList: true,
    forceSelection: true,
    createNewOnEnter: false,
    appClass: "main.label",
    triggers: {
        toBuffer: {
            cls: "x-form-clipboard-trigger",
            hidden: false,
            weight: -1,
            handler: "toClipboard"
        },
        create: {
            cls: "x-form-plus-trigger",
            hidden: true,
            handler: function() {
                NOC.launch(this.appClass, "new", {});
            }
        }
    },
    labelTpl: [
        '<span style="color: {fg_color1};background-color: {bg_color1};border-radius: 5px 0 0 5px;padding: 0 3px 0 3px;">{scope}</span>',
        '<span style="color: {fg_color2};background-color: {bg_color2};border-radius: 0 5px 5px 0;padding-right: 3px;">{value}</span>'
    ],
    listConfig: {
        itemTpl: [
            '<div data-qtip="{scope}::{value}">',
            '<span style="color: {fg_color1};background-color: {bg_color1};border-radius: 5px 0 0 5px;padding: 0 3px 0 3px;">{scope}</span>',
            '<span style="color: {fg_color2};background-color: {bg_color2};border-radius: 0 5px 5px 0;padding-right: 3px;">{value}</span>',
            '</div>'
        ]
    },
    listeners: {
        change: "onChange"
    },

    initComponent: function() {
        var me = this,
            store = me.store || {
                model: "NOC.core.LabelFieldModel",
                pageSize: 0,
                proxy: {
                    type: "rest",
                    url: '/main/label/ac_lookup/',
                    pageParam: "__page",
                    startParam: "__start",
                    limitParam: "__limit",
                    sortParam: "__sort",
                    extraParams: {
                        "__format": "ext"
                    },
                    reader: {
                        type: "json",
                        rootProperty: "data",
                        totalProperty: "total",
                        successProperty: "success"
                    }
                }
            },
            process = function(perms) {
                if(Ext.Array.contains(perms, "create")) {
                    me.getTrigger("create").show();
                }
            };

        Ext.apply(me, {
            store: store
        });

        if(NOC.permissions$.isLoaded()) {
            process(NOC.permissions$.getPermissions(me.appClass));
        } else {
            NOC.permissions$.subscribe({
                    key: this.appClass,
                    value: function(perms) {
                        process(perms);
                    }
                }
            );
        }
        me.callParent();
    },

    filterPicked: function(rec) {
        return !this.valueCollection.contains(rec) && !rec.get("is_protected");
    },

    onKeyDown: function(e) {
        var me = this,
            key = e.getKey(),
            inputEl = me.inputEl,
            rawValue = inputEl.dom.value,
            valueCollection = me.valueCollection,
            selModel = me.selectionModel,
            stopEvent = false,
            lastSelectionIndex;

        if(me.readOnly || me.disabled || !me.editable) {
            return;
        }

        if(valueCollection.getCount() > 0 && (rawValue === '' || (me.getCursorPosition() === 0 && !me.hasSelectedText()))) {
            lastSelectionIndex = (selModel.getCount() > 0) ? valueCollection.indexOf(selModel.getLastSelected()) : -1;

            if(key === e.BACKSPACE || key === e.DELETE) {
                if(lastSelectionIndex > -1) {
                    if(selModel.getCount() > 1) {
                        lastSelectionIndex = -1;
                    }
                    valueCollection.remove(Ext.Array.filter(selModel.getSelection(), function(el) {
                        return !el.get("is_protected")
                    }));
                } else {
                    if(!valueCollection.last().get("is_protected")) {
                        valueCollection.remove(valueCollection.last());
                    }
                }
                selModel.clearSelections();
                if(lastSelectionIndex > 0) {
                    selModel.select(lastSelectionIndex - 1);
                } else if(valueCollection.getCount()) {
                    selModel.select(valueCollection.last());
                }
                stopEvent = true;
            } else if(key === e.RIGHT || key === e.LEFT) {
                if(lastSelectionIndex === -1 && key === e.LEFT) {
                    selModel.select(valueCollection.last());
                    stopEvent = true;
                } else if(lastSelectionIndex > -1) {
                    if(key === e.RIGHT) {
                        if(lastSelectionIndex < (valueCollection.getCount() - 1)) {
                            selModel.select(lastSelectionIndex + 1, e.shiftKey);
                            stopEvent = true;
                        } else if(!e.shiftKey) {
                            selModel.deselectAll();
                            stopEvent = true;
                        }
                    } else if(key === e.LEFT && (lastSelectionIndex > 0)) {
                        selModel.select(lastSelectionIndex - 1, e.shiftKey);
                        stopEvent = true;
                    }
                }
            } else if(key === e.A && e.ctrlKey) {
                selModel.selectAll();
                stopEvent = e.A;
            }
        }

        if(stopEvent) {
            me.preventKeyUpEvent = stopEvent;
            e.stopEvent();
            return;
        }

        if(me.isExpanded && key === e.ENTER && me.picker.highlightedItem) {
            me.preventKeyUpEvent = true;
        }

        if(me.enableKeyEvents) {
            me.callParent(arguments);
        }

        if(!e.isSpecialKey() && !e.hasModifier()) {
            selModel.deselectAll();
        }
    },

    getMultiSelectItemMarkup: function() {
        var me = this,
            childElCls = (me._getChildElCls && me._getChildElCls()) || '';
        if(!me.multiSelectItemTpl) {
            if(!me.labelTpl) {
                me.labelTpl = '{' + me.displayField + '}';
            }
            me.labelTpl = me.getTpl('labelTpl');

            if(me.tipTpl) {
                me.tipTpl = me.getTpl('tipTpl');
            }

            me.multiSelectItemTpl = new Ext.XTemplate([
                '<tpl for=".">',
                '<li data-selectionIndex="{[xindex - 1]}" data-recordId="{internalId}" class="' + me.tagItemCls + childElCls + '"',
                '<tpl if="this.isProtected(values)"> style="padding-right: 5px"</tpl>',
                '<tpl if="this.isSelected(values)">',
                ' ' + me.tagSelectedCls,
                '</tpl>',
                '{%',
                'values = values.data;',
                '%}',
                me.tipTpl ? '" data-qtip="{[this.getTip(values)]}">' : '">',
                '<div class="' + me.tagItemTextCls + '">{[this.getItemLabel(values)]}</div>',
                '<tpl if="!is_protected">',
                '<div class="' + me.tagItemCloseCls + childElCls + '"></div>',
                '</tpl>',
                '</li>',
                '</tpl>',
                {
                    isProtected: function(rec) {
                        return rec.get("is_protected");
                    },
                    isSelected: function(rec) {
                        return me.selectionModel.isSelected(rec);
                    },
                    getItemLabel: function(values) {
                        // html encoding on backend
                        return me.labelTpl.apply(values);
                    },
                    getTip: function(values) {
                        return Ext.String.htmlEncode(me.tipTpl.apply(values));
                    },
                    strict: true
                }
            ]);
        }
        if(!me.multiSelectItemTpl.isTemplate) {
            me.multiSelectItemTpl = this.getTpl('multiSelectItemTpl');
        }

        return me.multiSelectItemTpl.apply(me.valueCollection.getRange());
    },

    setValue: function(value, add, skipLoad) {
        var me = this,
            valueStore = me.valueStore,
            valueField = me.valueField,
            record, len, i, valueRecord, cls;

        if(Ext.isEmpty(value)) {
            value = null;
        } else if(Ext.isString(value) && me.multiSelect) {
            value = value.split(me.delimiter);
        } else {
            value = Ext.Array.from(value, true);
        }

        if(value) {
            for(i = 0, len = value.length; i < len; i++) {
                record = value[i];
                if(!record || !record.isModel) {
                    valueRecord = valueStore.findExact(valueField, record);
                    if(valueRecord > -1) {
                        value[i] = valueStore.getAt(valueRecord);
                    } else {
                        valueRecord = me.findRecord(valueField, record);
                        if(!valueRecord) {
                            valueRecord = {};
                            valueRecord[me.valueField] = record.id;
                            valueRecord[me.displayField] = record;

                            cls = me.valueStore.getModel();
                            valueRecord = new cls(valueRecord);
                        }
                        if(valueRecord) {
                            value[i] = valueRecord;
                        }
                    }
                }
            }
        }
        return me.callParent([value, add]);
    },

    toClipboard: function(btn) {
        var writeText = function(btn) {
            var text = btn.getValue().join(","),
                tagsEl = btn.el.query(".x-tagfield-list"),
                selectElementText = function(el) {
                    var range = document.createRange(),
                        selection = window.getSelection();
                    range.selectNode(el);
                    selection.removeAllRanges();
                    selection.addRange(range);
                },
                listener = function(e) {
                    if(e.clipboardData && Ext.isFunction(e.clipboardData.setData)) {
                        e.clipboardData.setData("text/plain", text);
                    } else { // IE 11
                        clipboardData.setData("Text", text);
                    }
                    e.preventDefault();
                };
            selectElementText(tagsEl[0]);
            document.addEventListener("copy", listener);
            document.execCommand("copy");
            document.removeEventListener("copy", listener);
        };
        writeText(btn);
    },

    onChange: function(labelField, newVal, oldVal) {
        var me = this, diff;
        if(Ext.isEmpty(oldVal)) {
            return;
        }
        if(newVal.length < oldVal.length) {
            return;
        }
        diff = Ext.Array.difference(newVal, oldVal);
        Ext.Array.each(diff, function(item) {
            var toRemove, filtered,
                scope = me.valueCollection.getByKey(item).get("scope");
            if(!Ext.isEmpty(scope)) {
                filtered = Ext.Array.filter(newVal, function(item) {
                    return Ext.String.startsWith(item, scope);
                });
                toRemove = Ext.Array.remove(filtered, item);
                if(toRemove.length) {
                    newVal = Ext.Array.remove(newVal, toRemove[0]);
                }
            }
        });
        labelField.setValue(newVal);
    }
});
