"""Geo_Agent - Extraktion von Baugrunddaten aus Bohrprofil- und Laengsschnitt-PDFs.

Module:
    legend         - Parst die Legende des Bohrprofils (BODENARTEN + DIN-Sektionen).
    soil           - Bodenart-Klassifikation (grobe Klassen) + DIN-Token-Parsing.
    bohrprofil     - Blatt 1 (Geomodul) & Blatt 2 (Geomodul_Bodenschicht).
    laengsschnitt  - Blatt 3 (Geo_Tunnel) & Blatt 4 (Geo_Spec).
    excel_writer   - Schreibt die .xlsx exakt nach Geo_Template.
"""

__all__ = ["legend", "soil", "bohrprofil", "laengsschnitt", "excel_writer"]
