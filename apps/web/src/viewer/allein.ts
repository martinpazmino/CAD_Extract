// viewer.html: der Viewer allein. ?ifc=<url> laedt ein IFC, ?ueberhoehung=5 setzt die Ueberhoehung,
// ?bohrungen=<json-url> laedt Stecknadeln und Unterlage wie aus der App (Pruefungen, scripts/check.mjs).
// Eine IFC-Datei kann auch auf die Seite gezogen werden.
import "./viewer.css";
import { viewerStarten } from "./viewer";
import { rahmen } from "./rahmen";
import type { Args } from "./kanal";

const v = await viewerStarten(document.getElementById("app")!, { leerText: "Eine IFC-Datei hier ablegen oder links öffnen." });
const parameter = new URLSearchParams(location.search);
const f = Number(parameter.get("ueberhoehung"));
if ([1, 2, 5, 10, 20].includes(f)) rahmen.faktor = f;
const url = parameter.get("ifc");
if (url) await v.setzen({ ifc: url, ueberhoehung: rahmen.faktor });
const nadelUrl = parameter.get("bohrungen");
if (nadelUrl) await v.setzen((await (await fetch(nadelUrl)).json()) as Args);
