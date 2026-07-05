from __future__ import annotations

from html import escape
from pathlib import Path

from nutri_app.domain.web_portal import WebPortalItem, WebPortalSnapshot


class WebPortalService:
    def publish_static_portal(self, snapshot: WebPortalSnapshot, output_dir: Path) -> int:
        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "style.css").write_text(self._style(), encoding="utf-8")
        (output_dir / "index.html").write_text(self._index(snapshot), encoding="utf-8")
        (output_dir / "agenda.html").write_text(
            self._list_page("Agenda", snapshot.appointments),
            encoding="utf-8",
        )
        (output_dir / "publicacoes.html").write_text(
            self._list_page("Publicacoes", snapshot.publications),
            encoding="utf-8",
        )
        return 3

    def _index(self, snapshot: WebPortalSnapshot) -> str:
        cards = "\n".join(
            f"""
            <article class="card">
              <span>{escape(card.title)}</span>
              <strong>{escape(card.value)}</strong>
              <small>{escape(card.detail)}</small>
            </article>
            """
            for card in snapshot.cards
        )
        generated = (
            snapshot.generated_at.isoformat(timespec="seconds")
            if snapshot.generated_at
            else ""
        )
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nutri Clinic Pro - Portal Web</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header>
    <h1>Nutri Clinic Pro</h1>
    <nav>
      <a href="index.html">Inicio</a>
      <a href="agenda.html">Agenda</a>
      <a href="publicacoes.html">Publicacoes</a>
    </nav>
  </header>
  <main>
    <section class="hero">
      <h2>Portal Web da clinica</h2>
      <p>Visao inicial para operacao web, acompanhamento e publicacoes do paciente.</p>
      <small>Gerado em {escape(generated)}</small>
    </section>
    <section class="grid">{cards}</section>
  </main>
</body>
</html>
"""

    def _list_page(self, title: str, items: list[WebPortalItem]) -> str:
        rendered_items = "\n".join(
            f"""
            <li>
              <strong>{escape(item.title)}</strong>
              <span>{escape(item.description)}</span>
              <small>{escape(item.meta)}</small>
            </li>
            """
            for item in items
        )
        if not rendered_items:
            rendered_items = "<li><span>Nenhum registro disponivel.</span></li>"
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - Nutri Clinic Pro</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <nav>
      <a href="index.html">Inicio</a>
      <a href="agenda.html">Agenda</a>
      <a href="publicacoes.html">Publicacoes</a>
    </nav>
  </header>
  <main>
    <ul class="list">{rendered_items}</ul>
  </main>
</body>
</html>
"""

    def _style(self) -> str:
        return """
:root { color-scheme: light; font-family: Arial, sans-serif; }
body { margin: 0; background: #f5f7f8; color: #1d2a2e; }
header { display: flex; justify-content: space-between; align-items: center;
  padding: 18px 32px; background: #ffffff; border-bottom: 1px solid #d9e2e5; }
h1, h2 { margin: 0; }
nav { display: flex; gap: 16px; }
a { color: #176b5b; text-decoration: none; font-weight: 700; }
main { max-width: 1100px; margin: 0 auto; padding: 32px; }
.hero { padding: 28px 0; }
.hero p { max-width: 680px; line-height: 1.5; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px; }
.card { background: #ffffff; border: 1px solid #d9e2e5; border-radius: 8px;
  padding: 18px; display: grid; gap: 8px; }
.card strong { font-size: 28px; color: #176b5b; }
.list { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
.list li { background: #ffffff; border: 1px solid #d9e2e5; border-radius: 8px;
  padding: 16px; display: grid; gap: 6px; }
small { color: #5f6f75; }
"""
