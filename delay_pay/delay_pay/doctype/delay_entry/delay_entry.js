// Copyright (c) 2024, Precihole Sports Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Delay Entry", {
    start_date: function (frm) {
		if (frm.doc.start_date) {
			frm.trigger("set_end_date");
		}
	},
    set_end_date: function (frm) {
		frappe.call({
			method: 'hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date',
			args: {
				frequency: 'Monthly',
				start_date: frm.doc.start_date
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value('end_date', r.message.end_date);
				}
			}
		});
	},
});
