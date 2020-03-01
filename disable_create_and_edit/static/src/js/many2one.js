odoo.define('disable_create_and_edit.many2one_field', function (require) {
"use strict";

    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var dialogs = require("web.view_dialogs");
    var concurrency = require('web.concurrency');
    var _t = core._t;

    var FieldMany2One = relational_fields.FieldMany2One.include({
        init : function() {
            this._super.apply(this, arguments);
            this.limit = 7;
            this.orderer = new concurrency.DropMisordered();
//            this.can_create = ('can_create' in this.attrs ? JSON.parse(this.attrs.can_create) : true) &&
//                !this.nodeOptions.no_create;
            // Extra line - disable dialog create
            // -----------------------------------
            this.nodeOptions.no_create = true
            // -----------------------------------
            this.can_create = false;
            this.can_write = false;
//            this.can_write = 'can_write' in this.attrs ? JSON.parse(this.attrs.can_write) : true;
            this.nodeOptions = _.defaults(this.nodeOptions, {
                quick_create: false,
            });
            this.m2o_value = this._formatValue(this.value);
            this.recordParams = {fieldName: this.name, viewType: this.viewType};
            this.isDirty = false;
            this.lastChangeEvent = undefined;
        }
    });

});