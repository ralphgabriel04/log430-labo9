"""Génère RAPPORT.html (et permet l'export PDF via Edge headless) à partir de RAPPORT.md."""
import pathlib
import markdown

HERE = pathlib.Path(__file__).resolve().parent
md_text = (HERE / "RAPPORT.md").read_text(encoding="utf-8")

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists"],
    extension_configs={"codehilite": {"guess_lang": False, "noclasses": True}},
)

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", Calibri, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; max-width: 100%;
}
h1 { font-size: 20pt; color: #0b3d91; border-bottom: 3px solid #0b3d91;
     padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 14pt; color: #0b3d91; border-bottom: 1px solid #cdd7e8;
     padding-bottom: 4px; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12pt; color: #234; page-break-after: avoid; }
p, li { text-align: justify; }
code { font-family: "Cascadia Code", Consolas, monospace; font-size: 9pt;
       background: #f0f3f8; padding: 1px 4px; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #d6dde6; border-left: 4px solid #0b3d91;
      border-radius: 4px; padding: 10px 12px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.6pt; line-height: 1.35; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #b9c4d4; padding: 5px 8px; text-align: left; }
th { background: #0b3d91; color: #fff; }
tr:nth-child(even) td { background: #f3f6fb; }
blockquote { border-left: 4px solid #f0a500; background: #fff8e8; margin: 12px 0;
             padding: 6px 14px; color: #4a3b00; }
blockquote p { text-align: left; }
hr { border: none; border-top: 1px solid #d6dde6; margin: 18px 0; }
strong { color: #0b3d91; }
"""

html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Rapport Labo 09 - LOG430</title>
<style>{CSS}</style></head>
<body>{html_body}</body></html>"""

out = HERE / "RAPPORT.html"
out.write_text(html, encoding="utf-8")
print(f"HTML généré : {out}")
