import flet as ft

from data.db import init_db
from ui.home import build_home
from ui.scanner import build_scanner
from ui.mediqr_screen import build_mediqr
from ui.sehatsathi_screen import build_sehatsathi
from ui import theme


def load_config() -> dict:
    import json, os
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main(page: ft.Page):
    init_db()

    page.title = "AuraSafe"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = theme.BG
    page.padding = 0
    page.scroll = None
    page.window.icon = "assets/icon.png"

    config = load_config()
    current_view = {"name": "home"}

    nav_container = ft.Column(expand=True, spacing=0)

    def navigate(view_name: str):
        current_view["name"] = view_name
        render()

    def render():
        name = current_view["name"]
        if name == "home":
            body = build_home(page, navigate)
        elif name == "scanner":
            body = build_scanner(page, navigate, lambda: config)
        elif name == "mediqr":
            body = build_mediqr(page, navigate)
        elif name == "sehatsathi":
            body = build_sehatsathi(page, navigate)
        else:
            body = build_home(page, navigate)

        nav_container.controls = [
            ft.Container(content=body, expand=True),
            _bottom_nav(),
        ]
        page.update()

    def _bottom_nav():
        items = [
            ("home",       ft.Icons.HOME,            "Home"),
            ("scanner",    ft.Icons.QR_CODE_SCANNER,  "Scan"),
            ("mediqr",     ft.Icons.QR_CODE_2,        "MediQR"),
            ("sehatsathi", ft.Icons.HEALTH_AND_SAFETY,"Triage"),
        ]
        name = current_view["name"]

        def nav_item(view, icon, label):
            active = name == view
            color = theme.ACCENT if active else theme.TEXT_DIM
            return ft.GestureDetector(
                on_tap=lambda _, v=view: navigate(v),
                content=ft.Column(
                    [
                        ft.Icon(icon, color=color, size=22),
                        ft.Text(label, size=10, color=color),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                expand=True,
            )

        return ft.Container(
            content=ft.Row(
                [nav_item(v, i, l) for v, i, l in items],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            bgcolor=theme.SURFACE,
            border=ft.border.only(top=ft.BorderSide(1, theme.BORDER)),
            padding=ft.padding.symmetric(vertical=10, horizontal=8),
        )

    page.add(nav_container)
    render()


ft.app(target=main)
