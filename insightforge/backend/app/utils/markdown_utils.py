import markdown


def markdown_to_html(content: str) -> str:
    body = markdown.markdown(content, extensions=["tables", "fenced_code", "nl2br"])
    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.6; color: #222; }}
    h1, h2, h3 {{ color: #0f172a; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .low-confidence {{ color: #b91c1c; font-weight: 700; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
