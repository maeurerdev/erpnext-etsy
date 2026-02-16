frappe.ui.form.on("Etsy Shop", {
	refresh(frm) {

		// Login / Disconnect Button
        if (!frm.is_new()) {
			if (frm.doc.status === 'Disconnected') {
				frm.add_custom_button(__("Login with {} on Etsy", [frm.doc.shop_name]), async () => {
					if (frm.is_dirty()) {
						frappe.show_alert(__('Please save before logging in!'));
					} else {
						frappe.call({
							method: "initiate_web_application_flow",
							doc: frm.doc,
							callback: (r) => {
								window.open(r.message, "_blank");
							},
						});
					}
				});
			} else if (frm.doc.status === 'Connected') {
				frm.add_custom_button(__("Etsy Listings"), async () => {
					frappe.prompt([
							{
								label: __('Etsy Listing State'),
								fieldname: 'listing_state',
								fieldtype: 'Select',
								options: ['all', 'active', 'inactive', 'draft', 'sold_out', 'expired'],
								default: 'all',
								description: __('Listings with the selected state will be imported or updated.')
							},
							{
								label: __('Include Attributes'),
								fieldname: 'include_attributes',
								fieldtype: 'Check',
								default: 1,
								description: __('Also create or update Item Attributes of the selected Listings.')
							},
							{
								label: __('Include Items'),
								fieldname: 'include_items',
								fieldtype: 'Check',
								default: 0,
								description: __('Also create or update Items & Variants of the selected Listings.')
							}
						], (values) => {
							frappe.call({
								method: 'enqueue_import_listings',
								doc: frm.doc,
								args: {
									listing_state: values.listing_state,
									include_attributes: values.include_attributes,
									include_items: values.include_items
								},
								callback: () => {
									frappe.show_alert({
										message:__('Listing import has been queued.'),
										indicator:'blue'
									}, 5);
								},
								error: () => {
									frappe.show_alert({
										message:__('Failed to queue listing import!'),
										indicator:'red'
									}, 5);
								}
							});
						},
						__('Import Etsy Listings'),
						__('Import')
					)
				}, __('Import'));
				frm.add_custom_button(__("Sales History"), async () => {
					frappe.prompt([
							{
								label: __('From', null, 'date'),
								fieldname: 'min_date',
								fieldtype: 'Date',
								default: `${new Date().getFullYear()}-01-01`
							},
							{
								fieldname: 'column_break_1',
								fieldtype: 'Column Break'
							},
							{
								label: __('To', null, 'date'),
								fieldname: 'max_date',
								fieldtype: 'Date',
								default: frappe.datetime.nowdate()
							},
						], (values) => {
							if (values.min_date > values.max_date) {
								frappe.show_alert({
									message:__('From date must be before To date!'),
									indicator:'red'
								}, 5);
							} else {
								frappe.call({
									method: 'enqueue_import_receipts',
									doc: frm.doc,
									args: {
										min_date: values.min_date,
										max_date: values.max_date
									},
									callback: () => {
										frappe.show_alert({
											message:__('Sales import has been queued.'),
											indicator:'blue'
										}, 5);
									},
									error: () => {
										frappe.show_alert({
											message:__('Failed to queue sales import!'),
											indicator:'red'
										}, 5);
									}
								});
							}
						},
						__('Import Sales History'),
						__('Import')
					)
				}, __('Import'));

				frm.add_custom_button(__("Disconnect"), async () => {
					frappe.warn(__('Are you sure you want to proceed?'),
						__("You will need to login again with '{}' before next use!", [frm.doc.shop_name]),
						() => {
							// action to perform if proceeded
							frappe.call({
								method: "disconnect_etsy_shop",
								doc: frm.doc,
								callback: () => {
									frm.refresh();
								},
							});
						},
						__('Disconnect'),
						false // Sets dialog as minimizable
					)
				});

				frappe.db.get_single_value('Etsy Settings', 'etsy_enabled').then(etsy_enabled => {
					if (etsy_enabled == 0) {
						frm.set_intro(__("Synchronisation is not enabled! 'Etsy Settings > Enable Synchronisation'"), 'yellow');
					}
				})
			}
		}

		frm.toggle_display("api_credentials_section", !frm.is_new());

		frappe.db.get_single_value('Selling Settings', 'cust_master_name').then(cust_master_name => {
            if (cust_master_name === 'Customer Name') {
                frm.set_intro(__("It is not recommended to add new customers by name! 'Selling Settings > Customer Naming By' - using 'Naming Series' is preferred."), 'yellow');
            }
        })
        frappe.db.get_single_value('Selling Settings', 'customer_group').then(customer_group => {
			frm.toggle_reqd('customer_group', !Boolean(customer_group));
        })
        frappe.db.get_single_value('Stock Settings', 'item_group').then(item_group => {
			frm.toggle_reqd('item_group', !Boolean(item_group));
        })
		frappe.db.get_single_value('Stock Settings', 'stock_uom').then(stock_uom => {
			frm.toggle_reqd('stock_uom', !Boolean(stock_uom));
        })

	},
});
