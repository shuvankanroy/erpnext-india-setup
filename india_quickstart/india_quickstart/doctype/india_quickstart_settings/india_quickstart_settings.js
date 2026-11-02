frappe.ui.form.on('India Quickstart Settings', {
	refresh: function(frm) {
		// Populate states dropdown if empty
		if (!frm.doc.state || frm.fields_dict.state.get_options().length <= 1) {
			frm.call('get_gst_states').then(r => {
				if (r.message) {
					let states = Object.values(r.message);
					states.sort();
					frm.set_df_property('state', 'options', [''].concat(states));
					frm.refresh_field('state');
				}
			});
		}

		frm.fields_dict.run_setup_btn.$input && frm.fields_dict.run_setup_btn.$input.addClass('btn-primary');
	},

	gstin: function(frm) {
		let gstin = (frm.doc.gstin || '').trim().toUpperCase();
		if (gstin.length >= 12) {
			let pan = gstin.substring(2, 12);
			frm.set_value('pan', pan);
		}
	},

	run_setup_btn: function(frm) {
		if (!frm.doc.company) {
			frappe.msgprint(__('Please choose a Company first.'));
			return;
		}

		frappe.confirm(
			__('Are you sure you want to run India Quickstart automated setup for {0}?', [frm.doc.company]),
			function() {
				frappe.show_progress(__('Running India Quickstart'), 30, 100, __('Applying tax templates and compliance fields...'));
				frm.call('execute_setup').then(r => {
					frappe.hide_progress();
					if (r.message) {
						frappe.show_alert({
							message: __('India Settings successfully configured!'),
							indicator: 'green'
						}, 5);
						frm.reload_doc();
					}
				}).fail(() => {
					frappe.hide_progress();
				});
			}
		);
	}
});
