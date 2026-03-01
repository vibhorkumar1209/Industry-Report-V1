from pathlib import Path

def write_pdf(html_content: str, output_path: str) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        from weasyprint import HTML

        HTML(string=html_content).write_pdf(str(out))
        return str(out)
    except Exception:
        # Local mode can run without native WeasyPrint dependencies.
        return ""
