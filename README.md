PDFFakeDuplex – PDF Interleaver
================================

Kleines Python-Tool, um ein einseitiges Scan-PDF (erst alle Vorderseiten, danach alle Rückseiten – ggf. rückwärts) korrekt wieder zusammenzuführen.

Installation
------------

- Mit `pip` lokal installieren (erstellt das CLI `pdffake-duplex`):

```
pip install .
```

- Alternativ im Entwicklungsmodus:

```
pip install -e .
```

Voraussetzungen
---------------
- Python 3.8+
- pypdf: `pip install pypdf`

Verwendung
----------

Als CLI nach Installation:

```
pdffake-duplex input.pdf
```

Oder direkt mit Python (ohne Installation):

```
python pdffake_duplex.py input.pdf
```

Wichtigste Optionen:

- `-o, --output` – Ausgabedatei (Standard: `input.interleaved.pdf`)
- `-s, --split N` – Ab welcher Seite (1‑basiert) beginnt die zweite Hälfte? (Standard: Hälfte der Seiten)
- `-r, --reverse-second` – Zweite Hälfte vor dem Mischen umdrehen (typisch). Standard ist bereits „umdrehen“.
- `--no-reverse-second` – Erzwingt, dass die zweite Hälfte nicht umgedreht wird.
- `--pad-blank` – Kürzere Hälfte mit Leerseiten auffüllen, damit Paare aufgehen.
- `--dry-run` – Nichts schreiben, nur die geplante Seitenreihenfolge anzeigen.

Beispiele
---------

1) Standardfall (Vorderseiten zuerst, Rückseiten in umgekehrter Reihenfolge):

```
python pdffake_duplex.py scan.pdf
```

2) Rückseiten sind bereits vorwärts einsortiert:

```
python pdffake_duplex.py scan.pdf --no-reverse-second
```

3) Ungerade Seitenzahl / Trennposition angeben (z. B. zweite Hälfte startet bei Seite 17):

```
python pdffake_duplex.py scan.pdf --split 17
```

4) Vorschau der Zuordnung ohne Schreiben:

```
python pdffake_duplex.py scan.pdf --dry-run
```

Mit CLI entsprechend:

```
pdffake-duplex scan.pdf --dry-run
```

Hinweise
--------
- Das Tool geht standardmäßig davon aus, dass die zweite Hälfte rückwärts einsortiert ist (typischer Scanner-Workflow beim Stapelwenden). Mit `--no-reverse-second` kann dies umgestellt werden.
- Bei ungleichen Hälften kann `--pad-blank` eine Leerseite einfügen, damit die Paarbildung aufgeht.
- Leerseiten haben die Größe der ersten Seite des Dokuments.
