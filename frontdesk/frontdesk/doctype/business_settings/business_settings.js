frappe.ui.form.on("Business Settings", {
	refresh(frm) {
		render_preview(frm);
		render_section_manager(frm);
	},
	after_save(frm) {
		render_section_manager(frm);
	},
});

// ── Section Manager ───────────────────────────────────────────────────────────
// A Vue-powered drag-and-drop editor injected into the Content tab.
// Shows every section row with enable/disable toggle, type badge, and drag handle.
// "Add Section" opens a dialog to pick a type and set heading/content.
function render_section_manager(frm) {
	// Find the homepage_sections field wrapper
	let field = frm.get_field("homepage_sections");
	if (!field) return;

	// Inject a "Manage Sections" button above the child table
	if (field.$wrapper.find(".fd-section-mgr-btn").length) return; // already injected

	let $toolbar = $(`
		<div style="margin-bottom:0.75rem; display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;">
			<button class="btn btn-primary btn-xs fd-section-mgr-btn" type="button">
				<svg style="width:12px;height:12px;margin-right:4px;vertical-align:-1px" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
				Add Section
			</button>
			<button class="btn btn-default btn-xs fd-section-sort-btn" type="button">
				<svg style="width:12px;height:12px;margin-right:4px;vertical-align:-1px" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
				Reorder
			</button>
			<span style="color:#8a8f98;font-size:0.72rem;">Drag rows to reorder. Enable/disable each block. Add a "custom" row for freeform text + image.</span>
		</div>
	`);

	field.$wrapper.prepend($toolbar);

	$toolbar.find(".fd-section-mgr-btn").on("click", function () {
		open_add_section_dialog(frm);
	});

	$toolbar.find(".fd-section-sort-btn").on("click", function () {
		open_reorder_dialog(frm);
	});
}

const SECTION_TYPES = [
	{ value: "hero",         label: "Hero",          icon: "🏠", desc: "Full-width banner with tagline + CTA buttons" },
	{ value: "story",        label: "Story",         icon: "📖", desc: "Heading + rich text + optional image (split layout)" },
	{ value: "services",     label: "Services",      icon: "✂️", desc: "Service cards grid (pulled from Items)" },
	{ value: "how_it_works", label: "How It Works",  icon: "🔢", desc: "3-step numbered cards" },
	{ value: "gallery",      label: "Gallery",       icon: "🖼️", desc: "Image strip (from service images)" },
	{ value: "testimonials", label: "Testimonials",  icon: "💬", desc: "Customer quote cards" },
	{ value: "visit",        label: "Hours & Visit", icon: "📍", desc: "Opening hours, address, contact links" },
	{ value: "cta_band",     label: "CTA Band",      icon: "🎯", desc: "Full-width call-to-action strip" },
	{ value: "custom",       label: "Custom Block",  icon: "✏️", desc: "Freeform: any heading + rich text + optional image" },
];

function open_add_section_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: "Add Homepage Section",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "type_picker",
				label: "Section Type",
				options: `<div id="fd-type-picker" style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:0.5rem;">
					${SECTION_TYPES.map(t => `
						<div class="fd-type-card" data-val="${t.value}" style="
							cursor:pointer;border:2px solid #e2e6e9;border-radius:8px;
							padding:0.75rem;transition:border-color .15s,background .15s;
						">
							<div style="font-size:1.3rem;line-height:1;">${t.icon}</div>
							<div style="font-weight:600;margin:.3rem 0 .1rem;font-size:.85rem;">${t.label}</div>
							<div style="color:#8a8f98;font-size:.72rem;">${t.desc}</div>
						</div>
					`).join("")}
				</div>`,
			},
			{ fieldtype: "Data",      fieldname: "heading",      label: "Heading (optional)" },
			{ fieldtype: "Data",      fieldname: "subheading",   label: "Sub-heading (optional)" },
			{ fieldtype: "Text",      fieldname: "body_text",    label: "Body Text (optional — HTML allowed for custom blocks)" },
			{ fieldtype: "Attach Image", fieldname: "image",     label: "Image (optional)" },
			{
				fieldtype: "Select",  fieldname: "image_position", label: "Image Position",
				options: "right\nleft\ntop\nbackground", default: "right"
			},
			{ fieldtype: "Data",      fieldname: "button_label", label: "Button Label (optional)" },
			{ fieldtype: "Data",      fieldname: "button_link",  label: "Button Link (optional)" },
			{
				fieldtype: "Select",  fieldname: "layout_variant", label: "Layout",
				options: "default\nfull-width\nsplit\ncard-grid\ncentered", default: "default"
			},
			{ fieldtype: "Color",     fieldname: "background_color", label: "Background Color (optional)" },
		],
		primary_action_label: "Add Section",
		primary_action(values) {
			let type_card = d.$wrapper.find(".fd-type-card.selected");
			let sec_type = type_card.data("val");
			if (!sec_type) {
				frappe.msgprint("Please pick a section type.");
				return;
			}
			let row = frm.add_child("homepage_sections");
			row.section_type    = sec_type;
			row.enabled         = 1;
			row.heading         = values.heading || "";
			row.subheading      = values.subheading || "";
			row.body_text       = values.body_text || "";
			row.image           = values.image || "";
			row.image_position  = values.image_position || "right";
			row.button_label    = values.button_label || "";
			row.button_link     = values.button_link || "";
			row.layout_variant  = values.layout_variant || "default";
			row.background_color = values.background_color || "";
			frm.refresh_field("homepage_sections");
			d.hide();
			frappe.show_alert({ message: `"${SECTION_TYPES.find(t=>t.value===sec_type)?.label}" section added — Save to publish.`, indicator: "green" });
		},
	});

	// Wire up type card selection
	d.$wrapper.on("click", ".fd-type-card", function () {
		d.$wrapper.find(".fd-type-card").css({ "border-color": "#e2e6e9", "background": "" });
		$(this).css({ "border-color": "var(--primary,#6c63ff)", "background": "#f5f4ff" });
		d.$wrapper.find(".fd-type-card").removeClass("selected");
		$(this).addClass("selected");
	});

	d.show();
	// Pre-select "custom" as default
	d.$wrapper.find('.fd-type-card[data-val="custom"]').trigger("click");
}

function open_reorder_dialog(frm) {
	let rows = frm.doc.homepage_sections || [];
	if (!rows.length) {
		frappe.msgprint("No sections yet. Add some first.");
		return;
	}

	let items_html = rows
		.slice()
		.sort((a, b) => (a.idx || 0) - (b.idx || 0))
		.map((r, i) => {
			let meta = SECTION_TYPES.find(t => t.value === r.section_type) || { icon: "📄", label: r.section_type };
			let enabled_badge = r.enabled
				? `<span style="color:#2ecc71;font-size:.7rem;">● ON</span>`
				: `<span style="color:#e74c3c;font-size:.7rem;">● OFF</span>`;
			return `<div class="fd-sort-item" data-name="${r.name || ""}" data-idx="${i}"
				style="display:flex;align-items:center;gap:.75rem;padding:.6rem .75rem;
				border:1px solid #e2e6e9;border-radius:6px;margin-bottom:.35rem;
				background:#fff;cursor:grab;user-select:none;">
				<span style="font-size:1.1rem;line-height:1;">${meta.icon}</span>
				<span style="flex:1;font-weight:500;font-size:.85rem;">${meta.label}${r.heading ? " · " + r.heading : ""}</span>
				${enabled_badge}
				<svg style="width:14px;height:14px;color:#bbb;flex-shrink:0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
			</div>`;
		}).join("");

	let d = new frappe.ui.Dialog({
		title: "Reorder Homepage Sections",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "sort_area",
				options: `<div id="fd-sortable" style="min-height:100px;">${items_html}</div>
					<p style="color:#8a8f98;font-size:.72rem;margin-top:.75rem;">Drag rows to reorder, then click Save Order.</p>`,
			},
		],
		primary_action_label: "Save Order",
		primary_action() {
			// Read new order from DOM
			let new_order = [];
			d.$wrapper.find("#fd-sortable .fd-sort-item").each(function () {
				new_order.push($(this).data("name"));
			});
			// Re-assign idx on the form doc rows
			let rows_by_name = {};
			(frm.doc.homepage_sections || []).forEach(r => { rows_by_name[r.name] = r; });
			new_order.forEach((name, i) => {
				if (rows_by_name[name]) rows_by_name[name].idx = i + 1;
			});
			frm.refresh_field("homepage_sections");
			d.hide();
			frappe.show_alert({ message: "Order saved — click Save to publish.", indicator: "blue" });
		},
	});

	d.show();

	// Drag-and-drop using HTML5 draggable (no external lib needed)
	let sortable = d.$wrapper.find("#fd-sortable")[0];
	let dragged = null;
	sortable.addEventListener("dragstart", function (e) {
		dragged = e.target.closest(".fd-sort-item");
		dragged.style.opacity = "0.5";
		e.dataTransfer.effectAllowed = "move";
	});
	sortable.addEventListener("dragend", function () {
		if (dragged) dragged.style.opacity = "";
		dragged = null;
	});
	sortable.addEventListener("dragover", function (e) {
		e.preventDefault();
		let target = e.target.closest(".fd-sort-item");
		if (target && target !== dragged) {
			let rect = target.getBoundingClientRect();
			let mid = rect.top + rect.height / 2;
			if (e.clientY < mid) {
				sortable.insertBefore(dragged, target);
			} else {
				sortable.insertBefore(dragged, target.nextSibling);
			}
		}
	});
	// Make items draggable
	d.$wrapper.find(".fd-sort-item").attr("draggable", "true");
}

// ── Live Preview ──────────────────────────────────────────────────────────────
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

	load_preview(field);
}

function load_preview(field) {
	let frm = cur_frm;
	if (!frm) return;
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
