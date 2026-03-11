import datetime
import socket

import flet as ft

from data.db import get_scan_history
from ui import theme


def build_home(page: ft.Page, navigate):
    scan_hist = get_scan_history(5)

    # ── Feature cards ─────────────────────────────────────────────────────────
    def feature_card(icon, title, subtitle, color, on_tap):
        return ft.GestureDetector(
            on_tap=on_tap,
            content=ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color="white", size=28),
                        width=56, height=56,
                        bgcolor=color,
                        border_radius=16,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Container(width=14),
                    ft.Column([
                        ft.Text(title, size=15, weight=ft.FontWeight.W_700, color=theme.TEXT_PRI),
                        ft.Text(subtitle, size=12, color=theme.TEXT_SEC),
                    ], spacing=2, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=theme.TEXT_DIM),
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.all(16),
                border_radius=16,
                bgcolor=theme.SURFACE,
                border=ft.border.all(1, theme.BORDER),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            ),
        )

    # ── Offline check ─────────────────────────────────────────────────────────
    try:
        socket.getaddrinfo("world.openfoodfacts.org", 80)
        is_online = True
    except Exception:
        is_online = False

    status_chip = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.WIFI if is_online else ft.Icons.WIFI_OFF,
                size=14,
                color=theme.SAFE_COLOR if is_online else theme.DANGER_COLOR,
            ),
            ft.Text(
                "Online" if is_online else "Offline — Using Cache",
                size=12,
                color=theme.SAFE_COLOR if is_online else theme.DANGER_COLOR,
            ),
        ], spacing=6),
        bgcolor=theme.SURFACE2,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border=ft.border.all(1, theme.SAFE_COLOR if is_online else theme.DANGER_COLOR),
    )

    # ── Recent scans ──────────────────────────────────────────────────────────
    def history_tile(scan):
        color = theme.score_color(scan["overall_score"])
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(str(scan["overall_score"]), size=14, weight=ft.FontWeight.W_900, color="white"),
                    width=36, height=36, bgcolor=color, border_radius=8,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(scan["product_name"], size=13, color=theme.TEXT_PRI, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(scan["timestamp"][:10], size=11, color=theme.TEXT_DIM),
                ], spacing=1, expand=True),
                ft.Text(scan["verdict"], size=11, color=color),
            ]),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border_radius=10,
            bgcolor=theme.SURFACE2,
        )

    history_section = ft.Column([
        theme.section_title("Recent Scans", ft.Icons.HISTORY),
        ft.Container(height=6),
        *([history_tile(s) for s in scan_hist] if scan_hist
          else [ft.Text("No scans yet — try the Barcode Scanner!", size=13, color=theme.TEXT_DIM)]),
    ], spacing=6)

    content = ft.ListView([
        # Header
        theme.gradient_header_with_icon(
            "AuraSafe",
            "Your Humanitarian Safety Shield",
        ),
        ft.Container(height=16),
        ft.Container(
            padding=ft.padding.symmetric(horizontal=16),
            content=ft.Column([
                # Online status
                ft.Row([status_chip], alignment=ft.MainAxisAlignment.END),
                ft.Container(height=8),
                # Features
                theme.section_title("Features", ft.Icons.APPS),
                ft.Container(height=8),
                feature_card(
                    ft.Icons.QR_CODE_SCANNER,
                    "Product Guardian",
                    "Scan barcodes for hazard & allergen risks",
                    "#1565C0",
                    lambda _: navigate("scanner"),
                ),
                ft.Container(height=10),
                feature_card(
                    ft.Icons.QR_CODE_2,
                    "MediQR",
                    "Your portable medical identity",
                    "#00695C",
                    lambda _: navigate("mediqr"),
                ),
                ft.Container(height=10),
                feature_card(
                    ft.Icons.HEALTH_AND_SAFETY,
                    "SehatSathi",
                    "Voice-first symptom triage",
                    "#4A148C",
                    lambda _: navigate("sehatsathi"),
                ),
                ft.Container(height=24),
                history_section,
                ft.Container(height=20),
                # Emergency
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMERGENCY, color="white", size=20),
                        ft.Text("Call Emergency: 112", size=14, color="white", weight=ft.FontWeight.W_700),
                    ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=theme.DANGER_COLOR,
                    border_radius=14,
                    padding=ft.padding.all(16),
                    on_click=lambda _: page.launch_url("tel:112"),
                ),
                ft.Container(height=24),
            ], spacing=0),
        ),
    ], spacing=0, expand=True)

    return content
