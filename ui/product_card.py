import flet as ft
from ui import theme


def build_product_card(page: ft.Page, product: dict, score: dict, disposal: list, user_profile: dict):
    def score_bar(label: str, val: int, icon):
        color = theme.score_color(val)
        return ft.Column([
            ft.Row([
                ft.Icon(icon, size=14, color=theme.TEXT_SEC),
                ft.Text(label, size=12, color=theme.TEXT_SEC, expand=True),
                ft.Text(f"{val}/10", size=12, weight=ft.FontWeight.W_700, color=color),
            ]),
            ft.ProgressBar(
                value=val / 10,
                bgcolor=theme.SURFACE2,
                color=color,
                height=6,
            ),
        ], spacing=4)

    def ingredient_tile(m: dict):
        score_val = m.get("health_score")
        conf = m.get("confidence", "unknown")
        color = theme.score_color(score_val) if score_val else theme.TEXT_DIM
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(
                        str(score_val) if score_val else "?",
                        size=12,
                        color="white",
                        weight=ft.FontWeight.W_700,
                    ),
                    width=30, height=30,
                    bgcolor=color,
                    border_radius=6,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(
                        m.get("ingredient", "Unknown"),
                        size=13,
                        color=theme.TEXT_PRI,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row([
                        ft.Text(f"Match: {conf}", size=10, color=theme.TEXT_DIM),
                        ft.Container(width=8),
                        *([ft.Text(flag, size=10, color=theme.WARN_COLOR)
                           for flag in m.get("hazard_flags", [])[:2]]),
                    ]),
                ], spacing=2, expand=True),
            ]),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=10,
            bgcolor=theme.SURFACE2,
        )

    # ── Personal risk banner ─────────────────────────────────────────────────
    personal_risk = score.get("personal_risk", "SAFE")
    alerts = score.get("personal_alerts", [])
    personal_banner = ft.Container(visible=False)
    if personal_risk != "SAFE" and alerts:
        banner_color = theme.DANGER_COLOR if personal_risk == "UNSAFE_FOR_YOU" else theme.WARN_COLOR
        personal_banner = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="white", size=20),
                    ft.Text(
                        "⚠️ UNSAFE FOR YOU" if personal_risk == "UNSAFE_FOR_YOU" else "⚠️ CAUTION FOR YOU",
                        size=14, weight=ft.FontWeight.W_900, color="white",
                    ),
                ], spacing=8),
                *[ft.Text(a, size=12, color="white") for a in alerts],
            ], spacing=4),
            bgcolor=banner_color,
            border_radius=12,
            padding=ft.padding.all(14),
            visible=True,
        )

    # ── Allergens from OFF ───────────────────────────────────────────────────
    allergens = product.get("allergens", [])
    allergen_chips = ft.Row(
        [ft.Container(
            content=ft.Text(a, size=11, color="white"),
            bgcolor=theme.WARN_COLOR,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        ) for a in allergens],
        wrap=True, spacing=6, run_spacing=6,
    ) if allergens else ft.Text("None detected", size=12, color=theme.SAFE_COLOR)

    # ── Disposal section ─────────────────────────────────────────────────────
    disposal_items = ft.Column([
        ft.Text(d, size=12, color=theme.TEXT_SEC) for d in disposal
    ], spacing=6)

    ingr_details = score.get("ingredient_details", [])
    known = [m for m in ingr_details if m.get("health_score") is not None]

    verdict = score.get("verdict", "CAUTION")
    verdict_color = score.get("verdict_color", theme.WARN_COLOR)
    green = score.get("green_score", {}) or {}
    eco_grade = green.get("eco_grade", "?")
    eco_hazards = green.get("eco_hazards", [])
    eco_count = green.get("eco_hazard_count", 0)

    eco_grade_color_map = {
        "A": theme.SAFE_COLOR,
        "B": "#8BC34A",
        "C": "#FFC107",
        "D": theme.WARN_COLOR,
        "E": theme.DANGER_COLOR,
    }
    eco_grade_color = eco_grade_color_map.get(eco_grade, theme.TEXT_DIM)

    return ft.Column([
        # Product info header
        theme.card(ft.Row([
            ft.Column([
                ft.Text(product.get("title", "Unknown Product"), size=17, weight=ft.FontWeight.W_800, color=theme.TEXT_PRI, max_lines=2),
                ft.Text(product.get("brand", ""), size=13, color=theme.TEXT_SEC),
                ft.Container(height=6),
                ft.Row([
                    theme.badge(verdict, verdict_color),
                    ft.Container(width=6),
                    ft.Container(
                        content=ft.Text(f"Nutri: {product.get('nutri_grade', '?')}", size=11, color="white"),
                        bgcolor=theme.PRIMARY_LIGHT,
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                    ft.Container(width=6),
                    ft.Container(
                        content=ft.Text(f"Source: {product.get('source', 'OFF')}", size=10, color=theme.TEXT_DIM),
                        bgcolor=theme.SURFACE2,
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                ]),
            ], expand=True, spacing=0),
            ft.Container(width=12),
            theme.score_dial(score["overall"], size=70),
        ], alignment=ft.MainAxisAlignment.START)),

        personal_banner,

        # Score bars
        theme.card(ft.Column([
            theme.section_title("Hazard Scores", ft.Icons.ANALYTICS),
            ft.Container(height=10),
            score_bar("Health Risk", score["health_score"], ft.Icons.FAVORITE_BORDER),
            ft.Container(height=10),
            score_bar("Environmental Risk", score["env_score"], ft.Icons.ECO),
            ft.Container(height=8),
            ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, size=13, color=theme.TEXT_DIM),
                ft.Text(
                    f"Confidence: {score.get('confidence', '?')} · {len(known)}/{len(ingr_details)} ingredients matched",
                    size=11, color=theme.TEXT_DIM,
                ),
            ], spacing=6),
        ], spacing=0)),

        # Allergens
        theme.card(ft.Column([
            theme.section_title("Allergens (Open Food Facts)", ft.Icons.WARNING),
            ft.Container(height=8),
            allergen_chips,
        ], spacing=0)),

        # Ingredients
        theme.card(ft.Column([
            theme.section_title(f"Ingredient Analysis ({len(ingr_details)} found)", ft.Icons.SCIENCE),
            ft.Container(height=8),
            *([ingredient_tile(m) for m in ingr_details[:15]]
              if ingr_details
              else [ft.Text("No ingredient data available", size=13, color=theme.TEXT_DIM)]),
            ft.Container(height=4),
            ft.Text(
                "⚠️ AuraSafe is not a medical tool. Consult a professional for health decisions.",
                size=11, color=theme.TEXT_DIM, italic=True,
            ),
        ], spacing=6)),

        # Disposal
        theme.card(ft.Column([
            theme.section_title("Safe Disposal Guidance", ft.Icons.DELETE_OUTLINE),
            ft.Container(height=8),
            disposal_items,
        ], spacing=0)),

        # Green score
        theme.card(ft.Column([
            theme.section_title("Green Score", ft.Icons.ECO),
            ft.Container(height=8),
            ft.Row([
                theme.badge(f"Eco Grade: {eco_grade}", eco_grade_color),
                ft.Container(width=8),
                ft.Text(f"Hazards flagged: {eco_count}", size=12, color=theme.TEXT_SEC),
            ]),
            ft.Container(height=8),
            *(
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"{h.get('hazard', '').upper()} -> {h.get('element', '')} ({h.get('level', '')})",
                                size=11,
                                color=theme.TEXT_PRI,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(f"Tip: {h.get('tip', '')}", size=11, color=theme.SAFE_COLOR),
                        ], spacing=2),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        border_radius=8,
                        bgcolor=theme.SURFACE2,
                    )
                    for h in eco_hazards[:5]
                ]
                if eco_hazards
                else [ft.Text("No major environmental hazard keywords detected.", size=12, color=theme.TEXT_DIM)]
            ),
        ], spacing=4)),
    ], spacing=10)
