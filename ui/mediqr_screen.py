import flet as ft
import threading
import os
import tempfile
from ui import theme
from services import mediqr as mediqr_svc
from data.db import get_user_profile, save_user_profile


def build_mediqr(page: ft.Page, navigate):
    profile = get_user_profile()
    from services.camera_util import is_android, decode_qr_zxing

    # â”€â”€ QR state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    qr_image = ft.Image(src="", visible=False, width=220, height=220)
    qr_status = ft.Text("", size=13, color=theme.TEXT_SEC)
    _qr_temp_file = {"path": ""}

    def generate_qr(_):
        try:
            import os
            # Save to temp file and display via src= path
            tmp_path = mediqr_svc.generate_qr_file(profile)
            if _qr_temp_file["path"] and os.path.exists(_qr_temp_file["path"]):
                try:
                    os.unlink(_qr_temp_file["path"])
                except Exception:
                    pass
            _qr_temp_file["path"] = tmp_path
            qr_image.src = tmp_path
            qr_image.visible = True
            qr_status.value = "âœ… Show this QR code in an emergency"
        except Exception as e:
            qr_status.value = f"Error generating QR: {e}"
        page.update()

    # â”€â”€ Receiver scan state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    scan_result_container = ft.Column(spacing=8, visible=False)
    scan_status = ft.Text("", size=13, color=theme.TEXT_SEC)

    def show_profile_card(decoded: dict):
        scan_result_container.visible = True
        scan_result_container.controls.clear()

        blood = decoded.get("blood_group", "â€”")
        blood_color = {"A+": "#E53935","A-":"#B71C1C","B+":"#1E88E5","B-":"#0D47A1",
                       "O+":"#43A047","O-":"#1B5E20","AB+":"#8E24AA","AB-":"#4A148C"}.get(blood, theme.ACCENT)

        allergies = decoded.get("allergies", [])
        conditions = decoded.get("conditions", [])
        meds = decoded.get("medications", [])

        scan_result_container.controls.extend([
            theme.card(ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=theme.ACCENT, size=24),
                    ft.Column([
                        ft.Text(decoded.get("name", "Unknown"), size=18, weight=ft.FontWeight.W_800, color=theme.TEXT_PRI),
                        ft.Text(f"DOB: {decoded.get('dob', 'â€”')}", size=12, color=theme.TEXT_SEC),
                    ], spacing=1),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(blood, size=18, weight=ft.FontWeight.W_900, color="white"),
                        bgcolor=blood_color,
                        width=52, height=52,
                        border_radius=26,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                ], spacing=14),
            ], spacing=0)),
            # Allergies
            theme.card(ft.Column([
                theme.section_title("Allergies", ft.Icons.WARNING_AMBER),
                ft.Container(height=6),
                ft.Row(
                    [ft.Container(
                        content=ft.Text(a, size=11, color="white"),
                        bgcolor=theme.DANGER_COLOR, border_radius=12,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ) for a in allergies],
                    wrap=True, spacing=6, run_spacing=6,
                ) if allergies else ft.Text("None declared", size=12, color=theme.SAFE_COLOR),
            ], spacing=0)),
            # Conditions
            theme.card(ft.Column([
                theme.section_title("Medical Conditions", ft.Icons.MEDICAL_SERVICES),
                ft.Container(height=6),
                ft.Row(
                    [ft.Container(
                        content=ft.Text(c, size=11, color="white"),
                        bgcolor=theme.WARN_COLOR, border_radius=12,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ) for c in conditions],
                    wrap=True, spacing=6, run_spacing=6,
                ) if conditions else ft.Text("None declared", size=12, color=theme.SAFE_COLOR),
            ], spacing=0)),
            # Medications
            theme.card(ft.Column([
                theme.section_title("Current Medications", ft.Icons.MEDICATION),
                ft.Container(height=6),
                ft.Column(
                    [ft.Text(f"â€¢ {m}", size=12, color=theme.TEXT_PRI) for m in meds],
                    spacing=4,
                ) if meds else ft.Text("None declared", size=12, color=theme.SAFE_COLOR),
            ], spacing=0)),
            # Emergency contact
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALL, color="white", size=20),
                    ft.Text(
                        f"Emergency Contact: {decoded.get('emergency_contact', 'â€”')}",
                        size=13, color="white",
                    ),
                ], spacing=10),
                bgcolor=theme.DANGER_COLOR,
                border_radius=12,
                padding=ft.padding.all(14),
            ),
        ])
        page.update()



    # ── FilePicker for Android QR scan ──────────────────────────────────────
    def _on_qr_image_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            scan_status.value = "No image selected."
            page.update()
            return
        path = e.files[0].path
        if not path:
            scan_status.value = "Could not access the image file."
            page.update()
            return
        scan_status.value = "Decoding QR from image..."
        page.update()

        def _decode():
            found = decode_qr_zxing(path)
            if found:
                result = mediqr_svc.decode_qr_data(found)
                if result:
                    scan_status.value = "MediQR decoded successfully"
                    show_profile_card(result)
                else:
                    scan_status.value = "Not a valid MediQR code"
            else:
                scan_status.value = "No QR code found in image. Ensure it is clear and well-lit."
            page.update()

        threading.Thread(target=_decode, daemon=True).start()

    qr_picker = ft.FilePicker(on_result=_on_qr_image_picked)
    page.overlay.append(qr_picker)
    page.update()

    def on_scan_camera(_):
        from services.camera_util import scan_qr_from_camera, cv2_available

        # ── Android: use FilePicker ──────────────────────────────────────────
        if is_android():
            scan_status.value = "Opening camera..."
            page.update()
            qr_picker.pick_files(
                dialog_title="Capture or select a MediQR image",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False,
            )
            return

        # ── Desktop: live OpenCV camera ──────────────────────────────────────
        if not cv2_available():
            scan_status.value = "Camera unavailable — install OpenCV for desktop scanning"
            page.update()
            return

        try:
            scan_status.value = "Scanning... point camera at QR code"
            page.update()
            found = scan_qr_from_camera(timeout_frames=300)
            if found:
                result = mediqr_svc.decode_qr_data(found)
                if result:
                    scan_status.value = "MediQR decoded"
                    show_profile_card(result)
                else:
                    scan_status.value = "Not a valid MediQR code"
            else:
                scan_status.value = "No QR code detected — ensure it is visible and well lit"
            page.update()
        except Exception as e:
            scan_status.value = f"Camera error: {e}"
            page.update()

    # Chip row builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def chip_row(label, items_ref: list, suggestions: list):
        chips_row = ft.Row([], wrap=True, spacing=6, run_spacing=6)
        entry = ft.TextField(
            hint_text=f"Add {label}...",
            border_color=theme.BORDER,
            focused_border_color=theme.ACCENT,
            color=theme.TEXT_PRI,
            bgcolor=theme.SURFACE2,
            border_radius=10,
            text_size=13,
            dense=True,
        )

        def add_item(_):
            val = (entry.value or "").strip()
            if val and val not in items_ref:
                items_ref.append(val)
                refresh_chips()
                entry.value = ""
                page.update()

        def remove_item(val):
            if val in items_ref:
                items_ref.remove(val)
                refresh_chips()
                page.update()

        def refresh_chips():
            chips_row.controls = [
                ft.Container(
                    content=ft.Row([
                        ft.Text(v, size=12, color="white"),
                        ft.Container(width=4),
                        ft.GestureDetector(
                            content=ft.Icon(ft.Icons.CLOSE, size=14, color="white"),
                            on_tap=lambda _, v=v: remove_item(v),
                        ),
                    ], spacing=2),
                    bgcolor=theme.PRIMARY_LIGHT,
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                )
                for v in items_ref
            ]

        def add_suggestion(s):
            if s not in items_ref:
                items_ref.append(s)
                refresh_chips()
                page.update()

        refresh_chips()

        sug_chips = ft.Row([
            ft.Container(
                content=ft.Text(s, size=11, color=theme.ACCENT),
                border=ft.border.all(1, theme.ACCENT),
                border_radius=16,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                on_click=lambda _, s=s: add_suggestion(s),
                ink=True,
            )
            for s in suggestions[:6]
        ], wrap=True, spacing=6, run_spacing=6)

        return ft.Column([
            ft.Text(label, size=13, color=theme.TEXT_SEC, weight=ft.FontWeight.W_600),
            chips_row,
            ft.Row([entry, ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=theme.ACCENT, on_click=add_item)]),
            sug_chips,
        ], spacing=6)

    # â”€â”€ Profile fields â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    name_field = ft.TextField(
        value=profile.get("name", ""), hint_text="Full Name",
        border_color=theme.BORDER, focused_border_color=theme.ACCENT,
        color=theme.TEXT_PRI, bgcolor=theme.SURFACE2, border_radius=10,
        prefix_icon=ft.Icons.PERSON, text_size=14,
    )
    dob_field = ft.TextField(
        value=profile.get("dob", ""), hint_text="Date of Birth (YYYY-MM-DD)",
        border_color=theme.BORDER, focused_border_color=theme.ACCENT,
        color=theme.TEXT_PRI, bgcolor=theme.SURFACE2, border_radius=10,
        prefix_icon=ft.Icons.CALENDAR_TODAY, text_size=14,
    )
    ec_field = ft.TextField(
        value=profile.get("emergency_contact", ""), hint_text="Emergency Contact Number",
        border_color=theme.BORDER, focused_border_color=theme.ACCENT,
        color=theme.TEXT_PRI, bgcolor=theme.SURFACE2, border_radius=10,
        prefix_icon=ft.Icons.CALL, text_size=14,
    )

    blood_options = ["A+","A-","B+","B-","O+","O-","AB+","AB-"]
    blood_dd = ft.Dropdown(
        value=profile.get("blood_group", "") or None,
        options=[ft.dropdown.Option(b) for b in blood_options],
        border_color=theme.BORDER, focused_border_color=theme.ACCENT,
        fill_color=theme.SURFACE2,
        border_radius=10,
        label="Blood Group",
    )

    allergies_ref = list(profile.get("allergies", []))
    conditions_ref = list(profile.get("conditions", []))
    meds_ref = list(profile.get("medications", []))

    allergy_section = chip_row("Allergies", allergies_ref,
        ["Peanuts","Gluten","Dairy","Eggs","Soy","Fish","Shellfish","Tree Nuts"])
    condition_section = chip_row("Medical Conditions", conditions_ref,
        ["Diabetes","Hypertension","Asthma","Celiac Disease","Heart Disease","Lactose Intolerance"])
    med_section = chip_row("Current Medications", meds_ref,
        ["Aspirin","Ibuprofen","Metformin","Lisinopril","Atorvastatin","Levothyroxine"])

    save_banner = ft.Text("", size=13, color=theme.SAFE_COLOR)

    def save_profile(_):
        new_profile = {
            "name": name_field.value or "",
            "dob": dob_field.value or "",
            "blood_group": blood_dd.value or "",
            "allergies": list(allergies_ref),
            "conditions": list(conditions_ref),
            "medications": list(meds_ref),
            "emergency_contact": ec_field.value or "",
        }
        # Assign keys individually â€” avoids 'dict changed size during iteration'
        # that occurs when calling dict.update() while Flet iterates state internally
        for k, v in new_profile.items():
            profile[k] = v
        save_user_profile(new_profile)
        save_banner.value = "âœ… Profile saved!"
        page.update()

    # â”€â”€ Tab state (manual tabs) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    active_tab = {"v": 0}
    tab0_content = ft.Column(visible=True, expand=True,  scroll=ft.ScrollMode.AUTO)
    tab1_content = ft.Column(visible=False, expand=True, scroll=ft.ScrollMode.AUTO)
    tab0_btn = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.PERSON, size=16), ft.Text("My Profile", size=13, weight=ft.FontWeight.W_700)], spacing=6),
        bgcolor=theme.PRIMARY, border_radius=ft.border_radius.only(top_left=12, top_right=12),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        on_click=lambda _: switch_tab(0), ink=True,
    )
    tab1_btn = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.QR_CODE_SCANNER, size=16), ft.Text("Scan MediQR", size=13)], spacing=6),
        bgcolor=theme.SURFACE2, border_radius=ft.border_radius.only(top_left=12, top_right=12),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        on_click=lambda _: switch_tab(1), ink=True,
    )

    def switch_tab(idx: int):
        active_tab["v"] = idx
        tab0_content.visible = (idx == 0)
        tab1_content.visible = (idx == 1)
        tab0_btn.bgcolor = theme.PRIMARY if idx == 0 else theme.SURFACE2
        tab1_btn.bgcolor = theme.PRIMARY if idx == 1 else theme.SURFACE2
        page.update()

    # Build tab0 content
    tab0_content.controls = [
        ft.Container(height=8),
        name_field, ft.Container(height=8),
        dob_field, ft.Container(height=8),
        blood_dd, ft.Container(height=8),
        ec_field, ft.Container(height=16),
        allergy_section, ft.Container(height=12),
        condition_section, ft.Container(height=12),
        med_section, ft.Container(height=20),
        theme.primary_button("Save & Generate QR", on_click=save_profile, width=float("inf")),
        ft.Container(height=8),
        save_banner,
        ft.Container(height=16),
        ft.Container(height=1, bgcolor=theme.BORDER),
        ft.Container(height=12),
        ft.Text("Your MediQR Code", size=14, weight=ft.FontWeight.W_700, color=theme.TEXT_PRI),
        ft.Container(height=8),
        qr_image,
        qr_status,
        ft.Container(height=8),
        theme.outlined_button("Generate / Refresh QR", on_click=generate_qr, width=float("inf")),
        ft.Container(height=24),
    ]

    # Build tab1 content
    tab1_content.controls = [
        ft.Container(height=16),
        ft.Text("Scan a MediQR Code", size=16, weight=ft.FontWeight.W_700, color=theme.TEXT_PRI),
        ft.Text("For emergency responders or caregivers", size=12, color=theme.TEXT_SEC),
        ft.Container(height=16),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CAMERA_ALT, color="white", size=24),
                ft.Text("Scan MediQR with Camera", size=15, color="white", weight=ft.FontWeight.W_700),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            bgcolor=theme.PRIMARY,
            border_radius=14,
            padding=ft.padding.symmetric(vertical=18),
            on_click=on_scan_camera,
        ),
        ft.Container(height=8),
        scan_status,
        ft.Container(height=16),
        scan_result_container,
        ft.Container(height=24),
    ]

    return ft.Column([
        theme.gradient_header("MediQR", "Your Portable Medical Identity", ft.Icons.QR_CODE_2),
        ft.Container(
            content=ft.Column([
                # Tab bar
                ft.Row([tab0_btn, ft.Container(width=4), tab1_btn], spacing=0),
                ft.Container(
                    content=ft.Stack([tab0_content, tab1_content]),
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                ),
            ], spacing=0, expand=True),
            expand=True,
        ),
    ], spacing=0, expand=True)


