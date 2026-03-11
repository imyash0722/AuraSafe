import flet as ft

# ── Palette ──────────────────────────────────────────────────────────────────
PRIMARY      = "#1A237E"
PRIMARY_LIGHT= "#3949AB"
ACCENT       = "#00BCD4"
ACCENT_LIGHT = "#4DD0E1"
BG           = "#0D0D1A"
SURFACE      = "#1A1A2E"
SURFACE2     = "#252540"
BORDER       = "#2E2E4A"
TEXT_PRI     = "#FFFFFF"
TEXT_SEC     = "#B0BEC5"
TEXT_DIM     = "#546E7A"

SAFE_COLOR   = "#4CAF50"
WARN_COLOR   = "#FF9800"
DANGER_COLOR = "#F44336"
INFO_COLOR   = "#29B6F6"


def score_color(score: int) -> str:
    if score <= 3:
        return SAFE_COLOR
    if score <= 6:
        return WARN_COLOR
    return DANGER_COLOR


def card(content, padding=16, border_radius=16, bgcolor=SURFACE, **kwargs):
    return ft.Container(
        content=content,
        padding=ft.padding.all(padding),
        border_radius=border_radius,
        bgcolor=bgcolor,
        border=ft.border.all(1, BORDER),
        **kwargs,
    )


def section_title(text: str, icon=None):
    row_items = []
    if icon:
        row_items.append(ft.Icon(icon, size=18, color=ACCENT))
        row_items.append(ft.Container(width=8))
    row_items.append(ft.Text(text, size=14, weight=ft.FontWeight.W_700, color=TEXT_SEC))
    return ft.Row(row_items)


def badge(label: str, color: str, size=12):
    return ft.Container(
        content=ft.Text(label, size=size, color="white", weight=ft.FontWeight.W_700),
        bgcolor=color,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


def score_dial(score: int, size=80):
    color = score_color(score)
    return ft.Stack([
        ft.Container(
            width=size, height=size,
            border_radius=size // 2,
            bgcolor=SURFACE2,
            border=ft.border.all(3, color),
        ),
        ft.Container(
            width=size, height=size,
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Column([
                ft.Text(str(score), size=size // 3, weight=ft.FontWeight.W_900, color=color),
                ft.Text("/10", size=size // 8, color=TEXT_DIM),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
        ),
    ])


def primary_button(text: str, on_click=None, icon=None, width=None, bgcolor=PRIMARY):
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=18, color="white") if icon else ft.Container(),
            ft.Text(text, size=14, color="white", weight=ft.FontWeight.W_700),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
        width=width,
        on_click=on_click,
        ink=True,
    )


def outlined_button(text: str, on_click=None, icon=None, width=None):
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=18, color=ACCENT) if icon else ft.Container(),
            ft.Text(text, size=14, color=ACCENT, weight=ft.FontWeight.W_600),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        border=ft.border.all(1, ACCENT),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
        width=width,
        on_click=on_click,
        ink=True,
    )


def gradient_header(title: str, subtitle: str = "", icon=None):
    return ft.Container(
        gradient=ft.LinearGradient(
            colors=[PRIMARY, PRIMARY_LIGHT, ACCENT],
            begin=ft.alignment.Alignment(-1, -1),
            end=ft.alignment.Alignment(1, 1),
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=28),
        border_radius=ft.border_radius.only(bottom_left=24, bottom_right=24),
        content=ft.Column([
            ft.Row([
                ft.Icon(icon, color="white", size=28) if icon else ft.Container(),
                ft.Column([
                    ft.Text(title, size=22, weight=ft.FontWeight.W_900, color="white"),
                    ft.Text(subtitle, size=13, color="#B3E5FC") if subtitle else ft.Container(),
                ], spacing=2),
            ], spacing=12),
        ]),
    )


def loading_spinner(message="Loading..."):
    return ft.Column([
        ft.ProgressRing(width=48, height=48, stroke_width=4, color=ACCENT),
        ft.Text(message, size=13, color=TEXT_SEC),
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16)


def empty_state(icon, message: str, sub: str = ""):
    return ft.Column([
        ft.Icon(icon, size=64, color=BORDER),
        ft.Text(message, size=16, color=TEXT_SEC, text_align=ft.TextAlign.CENTER),
        ft.Text(sub, size=12, color=TEXT_DIM, text_align=ft.TextAlign.CENTER) if sub else ft.Container(),
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
