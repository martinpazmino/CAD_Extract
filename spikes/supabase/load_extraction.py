"""Kanonisches Extraktions-JSON (prototyp_v4.to_canonical) -> Supabase/Postgres (migrations/0001_core.sql).

    python load_extraction.py --dsn "host=... dbname=... user=..." --project "Name" --crs 25833 a.json [b.json ...]

Schreibt documents, extraction_runs (result = komplettes JSON, unveraenderlich), boreholes (collar als
PointZ im Projekt-CRS, transformiert mit ST_Transform), borehole_layers und groundwater_obs.
Schichten mit Dicke <= 0 verletzen den CHECK der Tabelle und werden als Issue gemeldet statt geladen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import psycopg2
from psycopg2.extras import Json


def load(cur, project_id: str, crs: int, data: dict) -> dict:
    doc = data["document"]
    cur.execute("""insert into documents (project_id, kind, storage_path, sha256, page_count)
                   values (%s, 'bohrprofil', %s, %s, %s)
                   on conflict (project_id, sha256) do update set page_count = excluded.page_count
                   returning id""", (project_id, f"source-pdfs/{doc['file']}", doc["sha256"], doc["pages"]))
    doc_id = cur.fetchone()[0]
    issues = [f"{b['code']}: {i}" for b in data["boreholes"] for i in b["issues"]]
    cur.execute("""insert into extraction_runs (document_id, parser_version, status, result, issues, metrics, finished_at)
                   values (%s, %s, 'done', %s, %s, %s, now()) returning id""",
                (doc_id, doc["parser_version"], Json(data), Json(issues),
                 Json({"boreholes": len(data["boreholes"]), "layers": sum(len(b["layers"]) for b in data["boreholes"])})))
    run_id = cur.fetchone()[0]
    stats = {"boreholes": 0, "layers": 0, "gw": 0, "skipped_layers": 0, "with_collar": 0}
    for b in data["boreholes"]:
        collar = None
        if b.get("x") is not None and b.get("crs_epsg"):
            collar = (b["x"], b["y"], b["gok_nhn"] or 0.0, b["crs_epsg"])
        cur.execute("""insert into boreholes (project_id, source_run_id, code, kind, collar, gok_nhn, end_depth, provenance)
                       values (%s, %s, %s, %s,
                               case when %s then extensions.ST_Transform(extensions.ST_SetSRID(
                                   extensions.ST_MakePoint(%s, %s, %s), %s), %s) end,
                               %s, %s, %s)
                       on conflict (project_id, code) do update set source_run_id = excluded.source_run_id,
                           collar = excluded.collar, gok_nhn = excluded.gok_nhn, end_depth = excluded.end_depth,
                           provenance = excluded.provenance, review = 'extracted'
                       returning id""",
                    (project_id, run_id, b["code"], b["kind"], collar is not None,
                     *(collar[:3] if collar else (0, 0, 0)), collar[3] if collar else 0, crs,
                     b["gok_nhn"], b["end_depth"], Json(b["provenance"] + [{"checks": b["checks"]}])))
        bh_id = cur.fetchone()[0]
        stats["boreholes"] += 1
        stats["with_collar"] += collar is not None
        cur.execute("delete from borehole_layers where borehole_id = %s", (bh_id,))
        cur.execute("delete from groundwater_obs where borehole_id = %s", (bh_id,))
        for ly in b["layers"]:
            if ly["bottom_depth"] <= ly["top_depth"]:
                stats["skipped_layers"] += 1
                continue
            cur.execute("""insert into borehole_layers (borehole_id, top_depth, bottom_depth, description_raw,
                               soil_class, hatch_class, confidence, provenance)
                           values (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (bh_id, ly["top_depth"], ly["bottom_depth"], ly["description_raw"],
                         ly["soil_class"] or "unbekannt", ly["hatch_class"], ly["confidence"],
                         Json(ly["provenance"] + ([{"issues": ly["issues"]}] if ly["issues"] else []))))
            stats["layers"] += 1
        for g in b["groundwater"]:
            cur.execute("""insert into groundwater_obs (borehole_id, depth, nhn, kind, provenance)
                           values (%s, %s, %s, %s, %s)""", (bh_id, g["depth"], g["nhn"], g["kind"], Json(b["provenance"])))
            stats["gw"] += 1
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--crs", type=int, default=25832)
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    with psycopg2.connect(a.dsn) as con, con.cursor() as cur:
        cur.execute("select id from projects where name = %s", (a.project,))
        row = cur.fetchone()
        if row is None:
            cur.execute("insert into projects (name, crs_epsg) values (%s, %s) returning id", (a.project, a.crs))
            row = cur.fetchone()
        for f in a.files:
            print(Path(f).name, load(cur, row[0], a.crs, json.loads(Path(f).read_text())))


if __name__ == "__main__":
    main()
