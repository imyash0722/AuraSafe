import flet as ft
from ui import theme
from services.triage import classify_symptoms, get_urgency_color, get_urgency_emoji, COMMON_SYMPTOMS
from services.voice_recog import start_voice_capture, voice_stack_available
from data.db import save_triage


def build_sehatsathi(page: ft.Page, navigate):
    selected_symptoms: list[str] = []
    stop_voice = {"fn": None}
    result_container = ft.Column(spacing=8, visible=False)
    custom_field = ft.TextField(
        hint_text="Describe your symptoms in your own words...",
        multiline=True, min_lines=2, max_lines=4,
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        color=theme.TEXT_PRI,
        bgcolor=theme.SURFACE2,
        border_radius=12,
        text_size=14,
    )
    status_text = ft.Text("", size=13, color=theme.TEXT_SEC)
    voice_status = ft.Text("", size=12, color=theme.TEXT_DIM)
    live_transcript = ft.Text("", size=12, color=theme.ACCENT, italic=True)
    chips_wrap = ft.Row([], wrap=True, spacing=6, run_spacing=8)

    def _ui_safe(fn):
        # Voice callbacks run on a background thread; marshal updates to UI thread.
        if hasattr(page, "call_from_thread"):
            page.call_from_thread(fn)
        else:
            fn()

    # ── Chip grid ─────────────────────────────────────────────────────────────
    def toggle_symptom(sym: str):
        if sym in selected_symptoms:
            selected_symptoms.remove(sym)
        else:
            selected_symptoms.append(sym)

    def build_chip(sym: str):
        is_selected = sym in selected_symptoms

        def on_chip_click(e, s=sym):
            toggle_symptom(s)
            refresh_chips()
            page.update()

        return ft.Container(
            content=ft.Text(sym, size=12, color="white" if is_selected else theme.TEXT_SEC),
            bgcolor=theme.PRIMARY if is_selected else theme.SURFACE2,
            border=ft.border.all(1, theme.PRIMARY if is_selected else theme.BORDER),
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            on_click=on_chip_click,
            ink=True,
        )

    def refresh_chips():
        chips_wrap.controls = [build_chip(s) for s in COMMON_SYMPTOMS]

    refresh_chips()

    def on_assess(_):
        all_symptoms = list(selected_symptoms)
        if custom_field.value and custom_field.value.strip():
            all_symptoms.append(custom_field.value.strip())

        if not all_symptoms:
            status_text.value = "⚠️ Please select or describe symptoms first"
            page.update()
            return

        result = classify_symptoms(all_symptoms)
        urgency = result["urgency"]
        color = get_urgency_color(urgency)
        emoji = get_urgency_emoji(urgency)
        save_triage(all_symptoms, urgency, result["guidance"])

        result_container.visible = True
        result_container.controls.clear()
        result_container.controls.extend([
            # Urgency badge
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"{emoji} {urgency}", size=28, weight=ft.FontWeight.W_900, color="white"),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text("URGENCY LEVEL", size=11, color="white", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                bgcolor=color,
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=24, vertical=20),
                alignment=ft.alignment.Alignment(0, 0),
            ),
            # Guidance
            theme.card(ft.Column([
                theme.section_title("What to do", ft.Icons.HEALTH_AND_SAFETY),
                ft.Container(height=8),
                ft.Text(result["guidance"], size=14, color=theme.TEXT_PRI),
                ft.Container(height=8),
                ft.Text(result["general_guidance"], size=13, color=theme.TEXT_SEC),
            ], spacing=0)),
            # Triggered symptoms
            *(
                [theme.card(ft.Column([
                    theme.section_title("Critical Symptoms Detected", ft.Icons.WARNING),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(s.title(), size=11, color="white"),
                            bgcolor=theme.DANGER_COLOR, border_radius=12,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        )
                        for s in result["triggered_red"]
                    ], wrap=True, spacing=6, run_spacing=6),
                ], spacing=0))]
                if result.get("triggered_red") else []
            ),
            # Emergency call if RED
            *(
                [ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMERGENCY, color="white", size=24),
                        ft.Text("CALL 112 NOW", size=18, color="white", weight=ft.FontWeight.W_900),
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=theme.DANGER_COLOR,
                    border_radius=16,
                    padding=ft.padding.symmetric(vertical=20),
                    on_click=lambda _: page.launch_url("tel:112"),
                )]
                if urgency == "RED" else []
            ),
            # Disclaimer
            theme.card(ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=theme.INFO_COLOR),
                    ft.Text("Disclaimer", size=13, color=theme.INFO_COLOR, weight=ft.FontWeight.W_600),
                ], spacing=6),
                ft.Container(height=4),
                ft.Text(
                    result.get("disclaimer", ""),
                    size=11, color=theme.TEXT_DIM, italic=True,
                ),
            ], spacing=0), bgcolor=theme.SURFACE2),
        ])
        status_text.value = ""
        page.update()

    def on_reset(_):
        selected_symptoms.clear()
        if stop_voice["fn"]:
            stop_voice["fn"]()
            stop_voice["fn"] = None
        custom_field.value = ""
        result_container.visible = False
        result_container.controls.clear()
        status_text.value = ""
        voice_status.value = ""
        live_transcript.value = ""
        refresh_chips()
        page.update()

    def on_voice_chunk(text: str):
        def _apply():
            existing = (custom_field.value or "").strip()
            custom_field.value = (existing + " " + text).strip() if existing else text
            voice_status.value = "Voice captured"
            live_transcript.value = ""
            page.update()

        _ui_safe(_apply)

    def on_voice_partial(text: str):
        def _apply():
            live_transcript.value = f"Live: {text}"
            voice_status.value = "Listening..."
            page.update()

        _ui_safe(_apply)

    def on_voice_error(err: str):
        def _apply():
            stop_voice["fn"] = None
            voice_status.value = err
            page.update()

        _ui_safe(_apply)

    def on_start_voice(_):
        if stop_voice["fn"]:
            voice_status.value = "Voice capture already running"
            page.update()
            return
        ok, reason = voice_stack_available()
        if not ok:
            voice_status.value = reason
            page.update()
            return
        voice_status.value = "Listening... speak symptoms and tap Stop Voice"
        live_transcript.value = ""
        page.update()
        stop_voice["fn"] = start_voice_capture(on_voice_chunk, on_voice_error, on_voice_partial)
        if stop_voice["fn"] is None:
            voice_status.value = "Unable to start voice capture"
            page.update()

    def on_stop_voice(_):
        if stop_voice["fn"]:
            stop_voice["fn"]()
            stop_voice["fn"] = None
            voice_status.value = "Voice capture stopped"
        else:
            if not voice_status.value:
                voice_status.value = "Voice capture not running"
        live_transcript.value = ""
        page.update()

    return ft.Column([
        theme.gradient_header("SehatSathi", "Voice-First Symptom Triage", ft.Icons.HEALTH_AND_SAFETY),
        ft.Container(height=0),
        ft.ListView([
            ft.Container(height=16),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Column([
                    theme.section_title("Select Symptoms", ft.Icons.CHECKLIST),
                    ft.Container(height=8),
                    chips_wrap,
                    ft.Container(height=14),
                    theme.section_title("Or describe in your own words", ft.Icons.EDIT),
                    ft.Container(height=6),
                    custom_field,
                    ft.Container(height=8),
                    ft.Row([
                        theme.primary_button("Start Voice", on_click=on_start_voice, icon=ft.Icons.MIC, width=150),
                        ft.Container(width=10),
                        theme.outlined_button("Stop Voice", on_click=on_stop_voice, icon=ft.Icons.MIC_OFF),
                    ]),
                    ft.Container(height=4),
                    voice_status,
                    ft.Container(height=2),
                    live_transcript,
                    ft.Container(height=2),
                    ft.Text(
                        "Voice capture requires a microphone and the Vosk model. Not available on Android.",
                        size=11,
                        color=theme.TEXT_DIM,
                    ),
                    ft.Container(height=12),
                    ft.Row([
                        theme.primary_button("Assess Urgency", on_click=on_assess, icon=ft.Icons.ASSESSMENT, width=200),
                        ft.Container(width=10),
                        theme.outlined_button("Reset", on_click=on_reset, icon=ft.Icons.REFRESH),
                    ]),
                    ft.Container(height=6),
                    status_text,
                    ft.Container(height=16),
                    result_container,
                    ft.Container(height=24),
                ], spacing=0),
            ),
        ], spacing=0, expand=True),
    ], spacing=0, expand=True)
