import threading

import flet as ft

from data import cache as product_cache
from data.db import get_user_profile, save_scan
from services import barcode_lookup, open_food_facts, risk_scorer
from services.camera_util import (
    cv2_available,
    is_android,
    scan_barcode_from_camera,
)
from ui import theme
from ui.product_card import build_product_card


_scanning = False


def build_scanner(page: ft.Page, navigate, get_config):
    result_view = ft.Ref[ft.Column]()
    barcode_field = ft.TextField(
        hint_text="Or type barcode manually...",
        border_color=theme.BORDER,
        focused_border_color=theme.ACCENT,
        color=theme.TEXT_PRI,
        bgcolor=theme.SURFACE2,
        border_radius=12,
        text_size=15,
        prefix_icon=ft.Icons.SEARCH,
    )
    status_text = ft.Text("", size=13, color=theme.TEXT_SEC)
    result_container = ft.Column(ref=result_view, spacing=10)
    loading = ft.Column([theme.loading_spinner("Fetching product data...")], visible=False)

    def do_lookup(barcode: str):
        barcode = barcode.strip()
        if not barcode:
            return

        loading.visible = True
        result_container.controls.clear()
        status_text.value = f"Looking up: {barcode}"
        page.update()

        product = product_cache.get_cached_product(barcode)
        from_cache = bool(product)
        if not product:
            product = open_food_facts.fetch_product(barcode)
            if product:
                api_key = get_config().get("barcode_api_key", "")
                if api_key:
                    bl_product = barcode_lookup.fetch_product(barcode, api_key)
                    product = barcode_lookup.merge_with_off(product, bl_product)
                product_cache.save_product(barcode, product)
            else:
                loading.visible = False
                status_text.value = ""
                result_container.controls.append(
                    theme.card(
                        ft.Column(
                            [
                                ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=theme.BORDER),
                                ft.Text("Product not found", size=16, color=theme.TEXT_SEC),
                                ft.Text("Try manual ingredient entry below", size=12, color=theme.TEXT_DIM),
                            ],
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    )
                )
                page.update()
                return

        user_profile = get_user_profile()
        score = risk_scorer.score_product(product, user_profile)
        disposal = risk_scorer.get_disposal_guidance(product, score)
        save_scan(barcode, product.get("title", "Unknown"), score["overall"], score["verdict"])

        loading.visible = False
        status_text.value = "Loaded from cache" if from_cache else "Data fetched successfully"

        card = build_product_card(page, product, score, disposal, user_profile)
        result_container.controls.clear()
        result_container.controls.append(card)
        page.update()

    def on_scan_click(_):
        code = barcode_field.value or ""
        if code.strip():
            threading.Thread(target=do_lookup, args=(code,), daemon=True).start()

    def on_camera_scan(_):
        global _scanning
        if _scanning:
            status_text.value = "Scan already in progress..."
            page.update()
            return
        _scanning = True

        if is_android():
            status_text.value = "Desktop-only camera mode enabled. Enter barcode manually on Android."
            page.update()
            _scanning = False
            return

        if not cv2_available():
            status_text.value = "Camera unavailable. Enter barcode manually and tap Search."
            page.update()
            _scanning = False
            return

        status_text.value = "Camera open. Point at barcode..."
        page.update()

        def _desktop_scan_worker():
            global _scanning
            try:
                found = scan_barcode_from_camera(timeout_frames=300)
                if found:
                    barcode_field.value = found
                    status_text.value = f"Scanned: {found}"
                    page.update()
                    threading.Thread(target=do_lookup, args=(found,), daemon=True).start()
                else:
                    status_text.value = "No barcode detected. Enter it manually and tap Search."
                    page.update()
            except Exception as ex:
                status_text.value = f"Camera error: {ex}"
                page.update()
            finally:
                _scanning = False

        threading.Thread(target=_desktop_scan_worker, daemon=True).start()

    return ft.Column(
        [
            theme.gradient_header("Product Scanner", "Scan or enter a barcode", ft.Icons.QR_CODE_SCANNER),
            ft.Container(height=16),
            ft.Container(
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.CAMERA_ALT, color="white", size=24),
                                    ft.Text("Scan with Camera", size=15, color="white", weight=ft.FontWeight.W_700),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10,
                            ),
                            bgcolor=theme.PRIMARY,
                            border_radius=14,
                            padding=ft.padding.symmetric(vertical=18),
                            on_click=on_camera_scan,
                        ),
                        ft.Container(height=12),
                        ft.Row(
                            [
                                ft.Container(expand=True, height=1, bgcolor=theme.BORDER),
                                ft.Text("  or  ", size=12, color=theme.TEXT_DIM),
                                ft.Container(expand=True, height=1, bgcolor=theme.BORDER),
                            ]
                        ),
                        ft.Container(height=8),
                        barcode_field,
                        ft.Container(height=8),
                        theme.primary_button("Search", on_click=on_scan_click, icon=ft.Icons.SEARCH, width=float("inf")),
                        ft.Container(height=6),
                        status_text,
                        ft.Container(height=12),
                        loading,
                        result_container,
                    ],
                    spacing=0,
                ),
            ),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
