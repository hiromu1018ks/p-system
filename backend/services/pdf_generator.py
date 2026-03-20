import os
from datetime import date

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

VALID_DOCUMENT_TYPES = [
    "permission_certificate",
    "land_lease_contract",
    "building_lease_contract",
    "renewal_notice",
]


def generate_pdf(document_type: str, case_data: dict, output_path: str) -> str:
    if document_type not in VALID_DOCUMENT_TYPES:
        raise ValueError(f"無効なドキュメント種別です: {document_type}")

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=False,
    )
    setup_template_filters(env)

    template = env.get_template(f"{document_type}.html")
    html_str = template.render(**case_data)

    css = CSS(string=f"""
        @font-face {{
            font-family: 'IPAexGothic';
            src: url('file://{FONT_DIR}/IPAexGothic.ttf');
        }}
        @font-face {{
            font-family: 'IPAexMincho';
            src: url('file://{FONT_DIR}/IPAexMincho.ttf');
        }}
        body {{
            font-family: 'IPAexGothic', sans-serif;
            font-size: 10.5pt;
            line-height: 1.6;
            color: #333;
            margin: 20mm 25mm;
        }}
        h1 {{
            font-size: 16pt;
            text-align: center;
            margin-bottom: 20pt;
            border-bottom: 2px solid #333;
            padding-bottom: 5pt;
        }}
        h2 {{
            font-size: 13pt;
            margin-top: 16pt;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 8pt 0;
        }}
        th, td {{
            border: 1px solid #999;
            padding: 4pt 8pt;
            text-align: left;
            font-size: 10pt;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .right {{ text-align: right; }}
        .center {{ text-align: center; }}
        .stamp-area {{
            margin-top: 30pt;
            text-align: right;
            padding-right: 40pt;
        }}
        .footer {{
            margin-top: 20pt;
            font-size: 9pt;
            color: #666;
        }}
    """)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    HTML(string=html_str).write_pdf(
        output_path,
        stylesheets=[css],
    )

    return output_path


def _format_date(date_str: str | None) -> str:
    if not date_str:
        return ""
    try:
        d = date.fromisoformat(date_str)
        return f"{d.year}年{d.month:02d}月{d.day:02d}日"
    except (ValueError, TypeError):
        return date_str


def _format_amount(amount: int | None) -> str:
    if amount is None:
        return "-"
    return f"{amount:,}円"


def setup_template_filters(env):
    env.filters["format_date"] = _format_date
    env.filters["format_amount"] = _format_amount
