odoo.define('account_financial_report.account_financial_report_backend', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var ControlPanelMixin = require('web.ControlPanelMixin');
var ReportWidget = require('account_financial_report.account_financial_report_widget');
var QWeb = core.qweb;

var report_backend = Widget.extend(ControlPanelMixin, {
    // Stores all the parameters of the action.
     events: {
        'click .o_account_financial_reports_print': 'print',
        'click .o_account_financial_reports_export': 'export',
        'click .o_account_financial_reports_fillprint': 'print_fillpdf',
         'click .o_account_financial_reports_zip': 'print_zip',
        'click .o_account_financial_reports_csv': 'print_csv',
        'click .o_account_financial_reports_xml': 'print_xml',
         'click .o_account_financial_reports_csv_vat': 'print_csv_vat',
        'click .o_account_financial_reports_csv_sales': 'print_csv_sales',
        'click .o_account_financial_reports_csv_purchase': 'print_csv_purchase',
    },
    init: function(parent, action) {
        this.actionManager = parent;
        this.given_context = {};
        this.odoo_context = action.context;
        this.controller_url = action.context.url;
        this.buttons = [];
        if (action.context.context) {
            this.given_context = action.context.context;
        }
        this.given_context.active_id = action.context.active_id || action.params.active_id;
        this.given_context.model = action.context.active_model || false;
        this.given_context.ttype = action.context.ttype || false;
        return this._super.apply(this, arguments);
    },
    willStart: function() {
        return $.when(this.get_html());
    },
    set_html: function() {
        var self = this;
        var def = $.when();
        if (!this.report_widget) {
            this.report_widget = new ReportWidget(this, this.given_context);
            def = this.report_widget.appendTo(this.$el);
        }
        def.then(function () {
            self.report_widget.$el.html(self.html);
        });
    },
    start: function() {
        this.set_html();
        var self = this;
        var cp_buttons = this._rpc({
                model: self.given_context.model,
                method: 'get_buttons',
                args: [self.given_context.active_id],
                context: self.odoo_context,
            })
            .then(function(result){
                return self.get_buttons(result);
            });
        return $.when(cp_buttons, this._super.apply(this, arguments)).then(function() {
            self.renderButtons(this.buttons);
            self.update_cp();
            //console.log("START", self);
        });
    },
    // Fetches the html and is previous report.context if any, else create it
    get_html: function() {
        var self = this;
        var defs = [];
        return this._rpc({
                model: this.given_context.model,
                method: 'get_html',
                args: [self.given_context],
                context: self.odoo_context,
            })
            .then(function (result) {
                self.html = result.html;
                defs.push(self.update_cp());
                return $.when.apply($, defs);
            });
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        var self = this;
        if (this.$buttons) {
            var status = {
                breadcrumbs: this.actionManager.get_breadcrumbs(),
                cp_content: {$buttons: this.$buttons},
            };
            return this.update_control_panel(status, {clear: true});
        }
    },
    do_show: function() {
        this._super();
        this.update_cp();
    },
    get_buttons: function(values) {
        this.buttons = values;
        //console.log("BUTTONS inside", values, this.buttons);
        return this.buttons;
    },
    renderButtons: function(buttons) {
        var self = this;
        console.log("BUTTONS RENDER", this.buttons, buttons);
        this.$buttons = $(QWeb.render("accountFinancialReporting.buttons", {buttons: this.buttons}));

        // bind actions
        _.each(this.$buttons.siblings('button'), function(el) {
            $(el).click(function() {
                self.$buttons.attr('disabled', true);
                return self._rpc({
                        model: self.given_context.model,
                        method: 'print_report',
                        args: [self.given_context.active_id, $(el).attr('data-ttype'), $(el).attr('data-id')],
                        context: self.odoo_context,
                    })
                    .then(function(result){
                        return self.do_action(result);
                    })
                    .always(function() {
                        self.$buttons.attr('disabled', false);
                    });
            });
        });
        return this.$buttons;
    },
    trigger_action: function(e) {
        e.stopPropagation();
        var self = this;
        var action = $(e.target).attr('action');
        var id = $(e.target).parents('td').data('id');
        var params = $(e.target).data();
        var context = new Context(this.odoo_context, params.actionContext || {}, {active_id: id});
        var type = $(e.target).attr('data-id');
        var ttype = $(e.target).attr('data-ttype');

        params = _.omit(params, 'actionContext');
        if (action) {
            return this._rpc({
                    model: this.given_context.model,
                    method: 'print_report',
                    args: [this.given_context.active_id, ttype, type],
                    context: self.odoo_context,
                })
                .then(function(result){
                    return self.do_action(result);
                });
        }
    },
    print: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'qweb-pdf', type],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_fillpdf: function() {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'fillpdf', type],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    export: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'xlsx', type],
            context: self.odoo_context,
        })
        .then(function(result){
            self.do_action(result);
        });
    },
    print_zip: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'zip', type],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_csv: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'csv', type],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_csv_vat: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'csv', 'vat'],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_csv_sales: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'csv', 'sales'],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_csv_purchase: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'csv', 'purchase'],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
    print_xml: function(ev) {
        var self = this;
        var type = $(ev.currentTarget).attr('data-id');
        this._rpc({
            model: this.given_context.model,
            method: 'print_report',
            args: [this.given_context.active_id, 'xml', type],
            context: self.odoo_context,
        }).then(function(result){
            self.do_action(result);
        });
    },
});

core.action_registry.add("account_financial_report_backend", report_backend);
return report_backend;
});
