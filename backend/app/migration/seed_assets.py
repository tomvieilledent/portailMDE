"""Images de démonstration générées en SVG : logos, avatars, cartes de visite, visuels de formation."""

from html import escape
from pathlib import Path

from app.services.storage import upload_root

_FONT = "font-family='Helvetica, Arial, sans-serif'"


def _write(category: str, name: str, svg: str) -> str:
    """Écrit le SVG dans le dossier public ``category`` et retourne le chemin relatif stocké en base."""
    folder = Path(upload_root()) / category
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(svg, encoding="utf-8")
    return f"{category}/{name}"


def _initials(text: str) -> str:
    """Deux initiales maximum, en majuscules."""
    words = [w for w in text.replace("&", " ").replace("-", " ").split() if w[0].isalnum()]
    return "".join(w[0] for w in words[:2]).upper()


def logo(slug: str, name: str, color: str, shape: str = "circle") -> str:
    """Logo carré (initiales sur fond coloré, motif selon ``shape``)."""
    initials = escape(_initials(name))
    motif = {
        "circle": f"<circle cx='256' cy='256' r='230' fill='{color}'/>",
        "square": f"<rect x='30' y='30' width='452' height='452' rx='60' fill='{color}'/>",
        "diamond": f"<rect x='86' y='86' width='340' height='340' rx='30' fill='{color}' "
        "transform='rotate(45 256 256)'/>",
        "bars": f"<rect width='512' height='512' fill='{color}'/>"
        "<rect x='0' y='380' width='512' height='40' fill='#ffffff' opacity='.25'/>"
        "<rect x='0' y='440' width='512' height='24' fill='#ffffff' opacity='.15'/>",
    }[shape]
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'>"
        f"<rect width='512' height='512' fill='#ffffff'/>{motif}"
        f"<text x='256' y='300' text-anchor='middle' font-size='170' font-weight='700' "
        f"fill='#ffffff' {_FONT}>{initials}</text></svg>"
    )
    return _write("logos", f"seed-{slug}.svg", svg)


def avatar(slug: str, first: str, last: str, color: str) -> str:
    """Avatar rond avec les initiales de la personne."""
    initials = escape(f"{first[:1]}{last[:1]}".upper())
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256'>"
        f"<rect width='256' height='256' fill='{color}'/>"
        f"<text x='128' y='160' text-anchor='middle' font-size='100' font-weight='600' "
        f"fill='#ffffff' {_FONT}>{initials}</text></svg>"
    )
    return _write("avatars", f"seed-{slug}.svg", svg)


def business_card(
    slug: str, name: str, job: str, company: str, email: str, phone: str, color: str
) -> str:
    """Carte de visite 85 × 55 mm : bandeau coloré, identité et coordonnées."""
    n, j, c, e, p = (escape(v) for v in (name, job, company, email, phone))
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 850 550'>"
        "<rect width='850' height='550' fill='#ffffff'/>"
        f"<rect width='60' height='550' fill='{color}'/>"
        f"<text x='120' y='170' font-size='58' font-weight='700' fill='#111827' {_FONT}>{n}</text>"
        f"<text x='120' y='225' font-size='34' fill='#4b5563' {_FONT}>{j}</text>"
        f"<text x='120' y='300' font-size='38' font-weight='700' fill='{color}' {_FONT}>{c}</text>"
        f"<text x='120' y='440' font-size='30' fill='#374151' {_FONT}>{e}</text>"
        f"<text x='120' y='485' font-size='30' fill='#374151' {_FONT}>{p}</text></svg>"
    )
    return _write("business-cards", f"seed-{slug}.svg", svg)


def training_picture(slug: str, title: str, color: str) -> str:
    """Visuel de formation (bandeau coloré avec le titre)."""
    t = escape(title)
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 400'>"
        f"<rect width='800' height='400' fill='{color}'/>"
        "<circle cx='700' cy='60' r='160' fill='#ffffff' opacity='.12'/>"
        "<circle cx='90' cy='380' r='120' fill='#ffffff' opacity='.1'/>"
        f"<text x='50' y='220' font-size='54' font-weight='700' fill='#ffffff' {_FONT}>{t}</text>"
        "</svg>"
    )
    return _write("trainings", f"seed-{slug}.svg", svg)
