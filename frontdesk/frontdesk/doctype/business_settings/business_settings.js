frappe.ui.form.on("Business Settings", {
	refresh(frm) {
		render_preview(frm);
	},
});

// Renders the Live Preview (Appearance tab) — shows the site with the
// CURRENT (unsaved) field values applied, so you see changes before saving.
// Pattern copied from Back House Website Settings.
function render_preview(frm) {
	let field = frm.get_field("live_preview");
	if (!field) return;

	let start_html =
		'<div style="padding:0.25rem 0 0.5rem; display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">\
			<button class="btn btn-default btn-xs" type="button" id="fd-trigger-preview" style="margin:0;">\
				<svg style="width:13px;height:13px;margin-right:4px;vertical-align:-2px" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>\
				Update preview\
			</button>\
			<button class="btn btn-default btn-xs" type="button" id="fd-reload-preview" style="margin:0;">Reload</button>\
			<span style="color:#8a8f98;font-size:0.75rem;">Shows your site with the current (unsaved) settings — press Save to publish.</span>\
		</div>\
		<div style="border:1px solid #e2e6e9;border-radius:8px;overflow:hidden;">\
			<iframe id="fd-preview-frame" style="width:100%;height:640px;border:0;background:#fff;display:block;" title="Live preview"></iframe>\
		</div>';

	field.$wrapper.empty().append($(start_html));

	field.$wrapper.find("#fd-trigger-preview, #fd-reload-preview").on("click", function () {
		load_preview(field);
	});

	// Load once on tab render so the tab shows the preview immediately.
	load_preview(field);
}

function load_preview(field) {
	let frm = cur_frm;
	if (!frm) return;
	// Collect current form values (including unsaved edits).
	let draft = {};
	$.each(frm.doc, function (k, v) {
		if (v === null || v === undefined || v === "") return;
		if (typeof v === "object" || typeof v === "boolean") return;
		draft[k] = String(v);
	});
	let url = "/?preview_settings=" + encodeURIComponent(JSON.stringify(draft)) + "&t=" + Date.now();
	let frame = field.$wrapper.find("#fd-preview-frame");
	frame.attr("src", url);
}
