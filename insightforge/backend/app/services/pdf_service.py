from pathlib import Path

from weasyprint import HTML


def write_pdf(html_content: str, output_path: str) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(str(out))
    return str(out)
