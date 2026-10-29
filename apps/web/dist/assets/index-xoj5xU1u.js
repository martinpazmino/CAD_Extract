const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./store-Be2Pz4vb.js","./preload-helper-Ct5FWWRu.js"])))=>i.map(i=>d[i]);
import"./viewer-C84WKf4Z.js";import{_ as je}from"./preload-helper-Ct5FWWRu.js";import{b as a,A as u,w as E,l as f,m as Oe,k as be,D as Ie}from"./lage-BJzdZVVN.js";import{S as s,n as p,o as j,v as B,a as y,m as T,p as Pe,s as O,b as ae,c as ge,d as g,z as se,e as pe,f as We,g as N,h as Ve,i as Ze,j as C}from"./store-Be2Pz4vb.js";import"./three.core-Dd2BBCN2.js";const ce={ocr:["OCR für Scans","Liest gescannte PDFs und Text, der nur als Linien gezeichnet ist (SHX). Langsamer; bei Vektor-PDFs nicht nötig."],beispiele:["Beispiele","Fertig ausgewertete Gutachten zum Ausprobieren. Echte Daten: Berlin (georeferenziert) und Talheim (ohne Koordinaten)."],pruefstand:["Prüfstand","Wie viele Bohrungen und Schichten Sie geprüft haben. Eine Korrektur zählt als geprüft. Der Stand wird beim Einchecken festgehalten."],alle_pruefen:["Alle geprüft","Markiert alle Schichten aller Bohrungen im Modell als geprüft – nur wenn Sie alles mit dem Gutachten verglichen haben. Zurücknehmen ist jederzeit möglich."],warnung:["Warnung","Eine Schicht, deren Bodenart nicht erkannt wurde (unklassifiziert). Bodenart wählen, den Vorschlag nach Norm übernehmen oder die Schicht als geprüft markieren."],bodenart:["Bodenart","Klasse für das Modell; Farbe nach DIN 4023 (Kies gelb, Sand orange, Schluff oliv, Ton violett …). Gleiche Bodenarten werden zu Einheiten verbunden."],norm:["Deutung nach Norm","Die Beschreibung aus dem PDF gelesen nach DIN 4023 / DIN EN ISO 14688-1: Hauptanteil, Nebenanteile (schwach ' / stark ¯), Kurzzeichen, Bodengruppe nach DIN 18196 (nur wenn genannt), Konsistenz. Steht auch im IFC (CPset_Bodenansprache)."],vorschlag:["Vorschlag nach Norm","Für eine unklassifizierte Schicht schlägt die Normen-Datenbank eine Bodenart aus der Beschreibung vor. Sie wird nur übernommen, wenn Sie klicken; danach gilt die Schicht als korrigiert."],geprueft:["Geprüft","Haken: Schicht mit dem Gutachten verglichen. Steht im IFC (Geprueft) und im Prüfstand."],tiefe:["Tiefe","Ober- und Unterkante in m unter Geländeoberkante (GOK). Geändertes wird als korrigiert markiert."],gok:["GOK","Ansatzhöhe der Bohrung in m NHN. Aus dem PDF oder hier eingetragen (manuell). Ohne GOK bei allen Bohrungen rechnet das Modell relativ (Gelände = 0 m)."],koordinaten:["Koordinaten","Rechts- und Hochwert der Bohrung; leer lassen, wenn die Lage im Schritt Lage auf dem Plan gesetzt wird."],entfernen:["Entfernen","Die Bohrung kommt nicht ins Modell (sie bleibt in der Liste unter „Entfernt“ und lässt sich wiederherstellen)."],quelle:["Quelle im PDF","Die Seite des Gutachtens, auf der die Bohrung erkannt wurde; der Rahmen zeigt die gewählte Schicht."],lage_art:["Art der Lage","Koordinaten: Bohrungen mit Rechts-/Hochwert (aus dem PDF, eingetragen oder auf dem Lageplan gesetzt). Reihe: ohne Koordinaten nebeneinander mit Abständen bzw. Stationen aus dem Längsschnitt."],unterlage:["Unterlage","Lageplan (Draufsicht) oder Längsschnitt (Seitenansicht) als PDF. Er liegt im Viewer unter den Bohrungen; nach dem Kalibrieren werden die Bohrungen daraufgezogen."],massstab:["Maßstab","Zwei Punkte auf dem Plan anklicken, deren Abstand Sie kennen (Maßstabsleiste, Bemaßung, zwei Bohrungen), und die wahre Länge in m eintragen. Oder den Maßstab 1:n direkt angeben."],bezug:["Bezugspunkt","Ein Punkt im Plan mit bekannter Koordinate (Koordinatenkreuz, Bohrung mit Koordinaten): anklicken und Rechts-/Hochwert eintragen – im Längsschnitt Station und Höhe NHN."],drehung:["Drehung","Winkel, um den der Plan gegen Norden gedreht ist (gegen den Uhrzeigersinn positiv). Nordpfeil nach oben = 0°; Nordpfeil 10° nach links geneigt = 10°."],hoehe:["Höhenmaßstab","Längsschnitte sind oft überhöht (z. B. Länge 1:500, Höhe 1:100). Ohne Angabe gilt der Längenmaßstab."],epsg:["Koordinatensystem (EPSG)","System der Rechts-/Hochwerte aus der Liste wählen: in Deutschland meist ETRS89 / UTM 32N (25832), im Osten 33N (25833), ältere Pläne Gauß-Krüger (Rechtswert 7-stellig, erste Ziffer = Zone); dazu Schweiz und Österreich. Passen die Werte nicht zum System (Ziffernzahl, Zonenkennung), erscheint ein Hinweis. Steht im IFC (IfcMapConversion)."],sperren:["Sperren","Schloss zu: der Plan liegt fest und ändert sich nicht mehr; jetzt die Bohrungen ziehen. Auf dem Lageplan nur in x/y, im Längsschnitt entlang der Station – in der Höhe nur, wenn das PDF keine GOK hat."],deckkraft:["Deckkraft","Wie stark der Plan die Szene überdeckt."],ohne_lage:["Ohne Lage","Bohrungen ohne Koordinaten: anklicken und dann in den gesperrten Plan klicken (Punkte setzen) – oder mit der Maus aus der Liste auf den Plan ziehen."],punkte:["Punkte setzen","Modus an, dann in den gesperrten Lageplan klicken: die gewählte Bohrung bekommt die Lage, danach ist die nächste ohne Lage dran (oder einen Chip anklicken). Mit „freien Punkt“ entsteht ein Punkt ◆, den Sie in der Liste einer Bohrung zuordnen. ✕ löscht einen Punkt bzw. die gesetzte Lage – im Viewer ebenso: Marke anklicken, Entf. Esc beendet den Modus."],reihe:["Reihe","Bohrungen in einer Linie. Abstand zum Vorgänger je Bohrung eintragen (BK1 → BK2 10 m, BK2 → BK3 15 m) oder eine Station; ohne Eintrag gilt der Standardabstand. Reihenfolge mit den Pfeilen."],standardabstand:["Standardabstand","Abstand zwischen Bohrungen, für die nichts eingetragen ist (nur zur Anschauung, im Modell als schematisch markiert)."],durchmesser:["Durchmesser","Dicke der Bohrsäulen im Viewer und im IFC (Darstellung, nicht der Bohrdurchmesser im Feld). Automatisch wächst er mit der Modellgröße, damit Säulen auf langen Trassen sichtbar bleiben."],einheiten:["Einheiten","Modelleinheiten verbinden gleiche Bodenarten zwischen den Bohrungen (Sand 1, Kies, Sand 2). Umbenennen oder Bodenarten zusammenlegen (z. B. „Sand, Kies“ als eine Einheit); Reihenfolge von oben nach unten."],methode:["Interpolation","IDW: gewichtetes Mittel der Nachbarbohrungen, ruhig und sicher. Dünnplatten-Spline: glatte Flächen mit Trend, gut bei geneigten Schichten."],puffer:["Puffer","Wie weit das Modell über die Bohrungen hinausreicht. Automatisch: halber Bohrabstand (5–100 m)."],raster:["Raster","Maschenweite der Schichtflächen. Automatisch: Gebietsgröße/40, bei großen Modellen gröber (höchstens 30 000 Knoten)."],basis:["Modellbasis","Unterkante des Modells in m NHN. Automatisch: tiefste Endteufe."],gok_relativ:["Fehlende GOK","Hat keine Bohrung eine GOK, rechnet das Modell relativ (Gelände = 0 m) – markiert im IFC."],auto:["Automatisch nachführen","Jede Änderung (Tabelle, Lage, Einheiten) rechnet das Modell sofort neu."],einchecken:["Einchecken","Hält den Prüfstand fest (Zeit, Zähler, Fingerabdruck des Modells, Kommentar). Das exportierte IFC trägt ihn (CPset_Baugrundmodell.Pruefstand)."],export:["Export","IFC 4.3 mit Prüfstand, Bodenansprache je Schicht und Beschreibungen je Einheit; dazu Prüfbericht und die Daten als JSON."],ueberhoehung:["Überhöhung","Höhen im Viewer mal Faktor, damit dünne Schichten sichtbar werden. Die Koordinaten bleiben echt."]};let S=null,ue=null;function q(){S?.remove(),S=null,ue=null}function Ue(e,t){e.preventDefault(),e.stopPropagation();const n=e.currentTarget;if(ue===n){q();return}q();const[i,r]=ce[t];S=document.createElement("div"),S.className="hilfe-blase",S.setAttribute("role","tooltip"),S.innerHTML="<strong></strong><p></p>",S.querySelector("strong").textContent=i,S.querySelector("p").textContent=r,document.body.append(S);const l=n.getBoundingClientRect(),o=S.getBoundingClientRect(),h=Math.min(Math.max(8,l.left+l.width/2-o.width/2),window.innerWidth-o.width-8),b=l.bottom+8+o.height>window.innerHeight?l.top-o.height-8:l.bottom+8;Object.assign(S.style,{left:`${h}px`,top:`${b}px`}),ue=n}document.addEventListener("click",e=>{S&&!S.contains(e.target)&&q()});document.addEventListener("keydown",e=>{e.key==="Escape"&&q()});const d=e=>a`<button type="button" class="hilfe" title=${ce[e][0]} aria-label=${`Hilfe: ${ce[e][0]}`}
    @click=${t=>Ue(t,e)}>?</button>`;let M=[],he=!0,Z=!1;async function Ee(e){for(;;){const t=await B(()=>y.auftrag(e));if(!t)return;if(s.auftrag=t,p(),t.fertig){s.auftrag=null;for(const n of t.fehler)T(n,"fehler",1e4);t.projekt?(M=[],await j(t.projekt,"bohrungen")):p();return}await new Promise(n=>setTimeout(n,600))}}async function Ce(){if(!M.length)return;const e=await B(()=>y.gutachten(M,he&&!!s.info?.ocr));e&&await Ee(e.id)}async function qe(e){const t=await B(()=>y.beispiel(e),"Beispiel wird geöffnet …");t?.projekt?await j(t.projekt,"bohrungen"):t?.auftrag&&await Ee(t.auftrag)}function ke(e){M=[...e??[]].filter(t=>/\.(pdf|json)$/i.test(t.name)),e?.length&&!M.length&&T("Bitte PDF-Dateien wählen (oder eine Extraktion als JSON).","warn"),p()}async function Je(e,t){confirm(`Projekt „${t}“ mit allen Korrekturen löschen? Das Gutachten selbst bleibt unberührt.`)&&(await B(()=>y.loeschen(e)),await Pe())}function Xe(){const e=s.auftrag,t=!!s.info?.ocr;return a`
    <div class="seite-mitte">
      <section class="karte gross">
        <h2>Bodengutachten auswerten</h2>
        <p class="leise">Bohrprofile, Schichtenverzeichnisse oder ganze Gutachten als PDF – Vektor oder Scan. Die Bohrungen
          werden erkannt; im nächsten Schritt prüfen und korrigieren Sie sie.</p>
        ${e?a`
          <div class="fortschritt-karte" aria-live="polite">
            <div class="kreisel klein"></div>
            <div>
              <strong>${e.stand.datei||e.dateien[0]}</strong>
              <span class="leise">Datei ${e.stand.nr}/${e.stand.dateien||e.dateien.length}
                ${e.stand.seiten?a` · Seite ${e.stand.seite}/${e.stand.seiten}${e.stand.klasse?` · ${e.stand.klasse}`:""}`:" · wird geöffnet …"}</span>
              <progress max=${e.stand.seiten||1} value=${e.stand.seite}></progress>
            </div>
          </div>`:a`
          <label class=${`ablage ${Z?"ueber":""}`}
            @dragover=${n=>{n.preventDefault(),Z=!0,p()}}
            @dragleave=${()=>{Z=!1,p()}}
            @drop=${n=>{n.preventDefault(),Z=!1,ke(n.dataTransfer?.files)}}>
            <input type="file" accept=".pdf,application/pdf,.json,application/json" multiple @change=${n=>ke(n.target.files)}>
            <span class="ablage-icon">⇪</span>
            <strong>${M.length?M.map(n=>n.name).join(", "):"PDF hierher ziehen oder klicken"}</strong>
            <span class="leise">${M.length?`${M.length} Datei(en) bereit`:"mehrere Dateien möglich (z. B. Anlagen 2–4) · auch eine Extraktion als JSON"}</span>
          </label>
          <div class="zeile">
            <label class="schalter" title=${t?"":"nicht installiert: pip install -r requirements-ocr.txt"}>
              <input type="checkbox" .checked=${he&&t} ?disabled=${!t} @change=${n=>{he=n.target.checked}}>
              OCR für Scans ${t?"":"(nicht installiert)"}
            </label>${d("ocr")}
            <span class="fueller"></span>
            <button class="primaer" ?disabled=${!M.length} @click=${Ce}>Auswerten →</button>
          </div>`}
      </section>

      <div class="zwei-spalten">
        <section class="karte">
          <h3>Beispiele ${d("beispiele")}</h3>
          <ul class="auswahl-liste">
            ${(s.info?.beispiele??[]).map(n=>a`
              <li><button class="link" ?disabled=${!!e} @click=${()=>qe(n.name)}>${n.titel}</button></li>`)}
          </ul>
        </section>
        <section class="karte">
          <h3>Zuletzt bearbeitet</h3>
          ${s.projekte.length?a`
            <table class="tabelle kompakt">
              <thead><tr><th>Projekt</th><th>Bohrungen</th><th>geprüft</th><th>geändert</th><th></th></tr></thead>
              <tbody>
                ${s.projekte.map(n=>a`
                  <tr>
                    <td><button class="link" @click=${()=>j(n.signatur)}>${n.name}</button>
                      <div class="leise klein">${n.dokumente.join(", ")}</div></td>
                    <td class="zahl">${n.bohrungen}</td>
                    <td class="zahl">${n.geprueft}${n.eincheckungen?a` · <span title="eingecheckt">✓${n.eincheckungen}</span>`:u}</td>
                    <td class="leise klein">${n.geaendert}</td>
                    <td><button class="symbol" title="Projekt löschen" aria-label="Projekt löschen" @click=${()=>Je(n.signatur,n.name)}>🗑</button></td>
                  </tr>`)}
              </tbody>
            </table>`:a`<p class="leise">Noch keine Projekte. Ein Projekt entsteht beim ersten Auswerten und wird automatisch gesichert.</p>`}
        </section>
      </div>
    </div>`}const U="Deutschland · ETRS89 / UTM (amtlich)",L="Deutschland · Gauß-Krüger (alt)",J=[{code:25832,name:"ETRS89 / UTM Zone 32N",gruppe:U,e:[22e4,101e4],n:[503e4,614e4],hinweis:"Rechtswert 6-stellig, die meisten Länder"},{code:25833,name:"ETRS89 / UTM Zone 33N",gruppe:U,e:[15e4,7e5],n:[509e4,613e4],hinweis:"Rechtswert 6-stellig, Osten (Berlin, Brandenburg, Sachsen, MV)"},{code:4647,name:"ETRS89 / UTM 32N mit Zone (32…)",gruppe:U,e:[3223e4,33e6],n:[52e5,614e4],hinweis:"Rechtswert 8-stellig, beginnt mit 32"},{code:5650,name:"ETRS89 / UTM 33N mit Zone (33…)",gruppe:U,e:[3315e4,3354e4],n:[52e5,613e4],hinweis:"Rechtswert 8-stellig, beginnt mit 33"},{code:31466,name:"DHDN / Gauß-Krüger Zone 2",gruppe:L,e:[23e5,27e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 2"},{code:31467,name:"DHDN / Gauß-Krüger Zone 3",gruppe:L,e:[33e5,37e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 3"},{code:31468,name:"DHDN / Gauß-Krüger Zone 4",gruppe:L,e:[43e5,47e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 4"},{code:31469,name:"DHDN / Gauß-Krüger Zone 5",gruppe:L,e:[531e4,57e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 5"},{code:2398,name:"Krassowski (42/83) / Gauß-Krüger Zone 4",gruppe:L,e:[43e5,47e5],n:[52e5,613e4],hinweis:"neue Länder vor ETRS89, Rechtswert beginnt mit 4"},{code:2399,name:"Krassowski (42/83) / Gauß-Krüger Zone 5",gruppe:L,e:[53e5,57e5],n:[52e5,613e4],hinweis:"neue Länder vor ETRS89, Rechtswert beginnt mit 5"},{code:3068,name:"DHDN / Soldner Berlin",gruppe:"Deutschland · andere",e:[-4e4,9e4],n:[-4e4,8e4],hinweis:"Berlin, alte Katasterkoordinaten (5-stellig)"},{code:2056,name:"CH1903+ / LV95",gruppe:"Schweiz",e:[245e4,287e4],n:[103e4,134e4],hinweis:"E 2 xxx xxx, N 1 xxx xxx"},{code:21781,name:"CH1903 / LV03",gruppe:"Schweiz",e:[45e4,87e4],n:[3e4,34e4],hinweis:"Y 6-stellig, X 5–6-stellig (alt)"},{code:31254,name:"MGI / Austria GK West",gruppe:"Österreich",e:[-11e4,17e4],n:[11e4,34e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31255,name:"MGI / Austria GK Central",gruppe:"Österreich",e:[-16e4,17e4],n:[9e4,46e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31256,name:"MGI / Austria GK East",gruppe:"Österreich",e:[-16e4,1e5],n:[1e5,48e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31257,name:"MGI / Austria GK M28 (BMN)",gruppe:"Österreich",e:[4e4,32e4],n:[11e4,34e4],hinweis:"Bundesmeldenetz West"},{code:31258,name:"MGI / Austria GK M31 (BMN)",gruppe:"Österreich",e:[29e4,62e4],n:[9e4,46e4],hinweis:"Bundesmeldenetz Mitte"},{code:31259,name:"MGI / Austria GK M34 (BMN)",gruppe:"Österreich",e:[59e4,85e4],n:[1e5,48e4],hinweis:"Bundesmeldenetz Ost"},{code:32632,name:"WGS 84 / UTM Zone 32N",gruppe:"GPS (WGS 84)",e:[22e4,101e4],n:[503e4,614e4],hinweis:"wie ETRS89 / UTM 32N (Abweichung < 1 m)"},{code:32633,name:"WGS 84 / UTM Zone 33N",gruppe:"GPS (WGS 84)",e:[15e4,7e5],n:[509e4,613e4],hinweis:"wie ETRS89 / UTM 33N (Abweichung < 1 m)"}],Qe=new Map(J.map(e=>[e.code,e]));function me(e){return e?Qe.get(e)??null:null}function De(e){if(!e)return"ohne System (lokal)";const t=me(e);return t?`EPSG ${e} · ${t.name}`:`EPSG ${e} (nicht in der Liste)`}const Le=(e,t,n)=>t>=e.e[0]&&t<=e.e[1]&&n>=e.n[0]&&n<=e.n[1];function Ye(e,t){return e===null||t===null||!Number.isFinite(e)||!Number.isFinite(t)?[]:J.filter(n=>n.gruppe!=="GPS (WGS 84)"&&Le(n,e,t))}function Ae(e,t,n){if(t===null||n===null||!Number.isFinite(t)||!Number.isFinite(n))return null;const i=Ye(t,n),r=i.slice(0,3).map(o=>`${o.code} (${o.name})`).join(", ");if(!e)return i.length?{ok:!1,text:`Kein System gewählt – die Werte passen zu ${r}.`}:null;const l=me(e);return l?Le(l,t,n)?{ok:!0,text:`passt zu EPSG ${e} (${l.hinweis})`}:{ok:!1,text:i.length?`Rechts-/Hochwert passen nicht zu EPSG ${e} (${l.hinweis}), aber zu ${r}.`:"Rechts-/Hochwert passen zu keinem System der Liste – Ziffern prüfen (z. B. fehlende Zonenkennung)."}:{ok:!1,text:`EPSG ${e} ist nicht in der Liste – bitte prüfen.`}}function Ke(e,t,n="Koordinatensystem"){const i=[...new Set(J.map(l=>l.gruppe))],r=e!==null&&!me(e);return a`
    <select class="epsg" aria-label=${n} title=${De(e)}
      @change=${l=>{const o=l.target.value;t(o===""?null:Number(o))}}>
      <option value="" .selected=${e===null}>– ohne (lokal) –</option>
      ${r?a`<option value=${String(e)} .selected=${!0}>EPSG ${e} – nicht in der Liste ⚠</option>`:u}
      ${i.map(l=>a`
        <optgroup label=${l}>
          ${J.filter(o=>o.gruppe===l).map(o=>a`
            <option value=${String(o.code)} .selected=${o.code===e}>${o.code} · ${o.name}</option>`)}
        </optgroup>`)}
    </select>`}const R=(e,t=2)=>e.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});function Ge(e){for(const t of[.5,1,2,5,10,20,50,100])if(e/t<=12)return t;return 200}function en(e,t){const n=Math.max(1,...e.map(c=>c.bis)),i=12,r=(t.hoehe-i-14)/n,l=34,o=46,h=Ge(n),b=[];for(let c=0;c<=n+1e-9;c+=h)b.push(c);return a`<svg class="saeule" viewBox="0 0 150 ${t.hoehe}" width="150" height=${t.hoehe} role="img" aria-label="Bohrsäule">
    <defs>
      <pattern id="schraffur-warn" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="6" height="6" fill="#e6e6e6"></rect><line x1="0" y1="0" x2="0" y2="6" stroke="#f0a33a" stroke-width="3"></line>
      </pattern>
    </defs>
    ${b.map(c=>E`
      <line x1=${l-5} x2=${l} y1=${i+c*r} y2=${i+c*r} class="achse"></line>
      <text x=${l-7} y=${i+c*r+3} class="achse-text" text-anchor="end">${R(c,h<1?1:0)}</text>`)}
    <line x1=${l} x2=${l} y1=${i} y2=${i+n*r} class="achse"></line>
    ${e.map(c=>E`
      <g class=${`schicht ${c.k===t.gewaehlt?"gewaehlt":""} ${c.warn?"warn":""}`} @click=${()=>t.waehlen?.(c.k)}>
        <title>${c.titel}</title>
        <rect x=${l+4} y=${i+c.von*r} width=${o} height=${Math.max(1,(c.bis-c.von)*r)}
          fill=${c.warn?"url(#schraffur-warn)":c.farbe}></rect>
        ${c.geprueft?E`<text x=${l+o+9} y=${i+(c.von+c.bis)/2*r+4} class="haken">✓</text>`:u}
        ${(c.bis-c.von)*r>11?E`<text x=${l+o+22} y=${i+c.bis*r-2} class="tiefe">${R(c.bis)}</text>`:u}
      </g>`)}
  </svg>`}function nn(e,t){const n=[...e.bohrungen].sort((m,W)=>m.x-W.x||m.y-W.y);if(!n.length)return u;const i=new Map(e.einheiten.map(m=>[m.name,m.farbe])),r=Math.max(...n.map(m=>m.gok)),l=Math.min(...n.map(m=>m.endteufe_nhn)),o=22,h=44,b=Math.max(38,Math.min(70,900/n.length)),c=h+n.length*b+10,v=(t.hoehe-o-10)/Math.max(1,r-l),w=m=>o+(r-m)*v,I=Ge(r-l),fe=[];for(let m=Math.ceil(l/I)*I;m<=r+1e-9;m+=I)fe.push(m);return a`<svg class="einheitenprofil" viewBox="0 0 ${c} ${t.hoehe}" width=${c} height=${t.hoehe} role="img"
      aria-label="Einheiten je Bohrung">
    ${fe.map(m=>E`
      <line x1=${h-4} x2=${c} y1=${w(m)} y2=${w(m)} class="raster"></line>
      <text x=${h-6} y=${w(m)+3} class="achse-text" text-anchor="end">${R(m,I<1?1:0)}</text>`)}
    ${n.map((m,W)=>{const V=h+W*b+b*.2,le=b*.6;return E`
        <text x=${V+le/2} y=${o-8} class="code" text-anchor="middle">${m.code}</text>
        ${m.einheiten.filter(z=>z.status==="vorhanden"&&z.ok_modell-z.uk_modell>.001).map(z=>E`
          <rect x=${V} y=${w(z.ok_modell)} width=${le} height=${Math.max(.8,(z.ok_modell-z.uk_modell)*v)}
            fill=${i.get(z.einheit)??"#ccc"} class=${`einheit ${t.gewaehlt===z.einheit?"gewaehlt":""}`}
            @click=${()=>t.waehlen?.(z.einheit)}>
            <title>${m.code}: ${z.einheit} ${R(z.ok_modell)} bis ${R(z.uk_modell)} m NHN</title>
          </rect>`)}
        <line x1=${V-3} x2=${V+le+3} y1=${w(m.endteufe_nhn)} y2=${w(m.endteufe_nhn)} class="endteufe"></line>`})}
  </svg>`}const X=(e,t=2)=>e==null?"":e.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),de=e=>{const t=e.target.value.trim().replace(",",".");return t===""?null:Number(t)},tn=[["boden","Böden"],["organisch","Organisch"],["geologisch","Geologische Benennung"],["fels","Fels"],["anthropogen","Anthropogen"],["unbekannt","Nicht klassifiziert"]];let Q=null,re="",_=.5,ve=!1;function Y(e){const t=O(),n=t.findIndex(r=>r.id===s.bid),i=t[Math.min(t.length-1,Math.max(0,n+e))];i&&ae(i.id)}function Fe(){const e=O(),t=ge(e.findIndex(n=>n.id===s.bid));t&&ae(t)}async function He(){const e=s.bid;if(!await g([{op:"bohrung_pruefen",id:e,wert:!0}],{leise:!0}))return;const t=ge(O().findIndex(n=>n.id===e));t&&t!==e&&await ae(t)}async function we(e){const t=s.z.pruefstand,n=e?`Alle Schichten aller ${t.bohrungen[1]} Bohrungen als geprüft markieren?`:"Die Prüfung aller Bohrungen zurücknehmen?";confirm(n)&&await g([{op:"alle_pruefen",wert:e}])}window.addEventListener("keydown",e=>{if(s.schritt!=="bohrungen"||e.ctrlKey||e.metaKey||e.altKey||e.target?.closest?.("input, select, textarea, [contenteditable]"))return;const n=e.key.toLowerCase();if(e.key==="ArrowDown"||n==="j")Y(1);else if(e.key==="ArrowUp"||n==="k")Y(-1);else if(n==="n")Fe();else if(n==="g")He();else return;e.preventDefault()});async function an(e,t){const n=Number(e.id.split(":")[0]),i=(t[0]?.quelle.seite??e.seite)-1,r=`${s.sig}/${n}/${i}`;if(Q?.schluessel===r||re===r||!s.z?.dokumente[n]?.pdf)return;re=r;const l=await B(()=>y.seite(s.sig,n,i));re="",l&&(Q={schluessel:r,daten:l},p())}function sn(e){return e.entfernt?a`<span class="zeichen raus" title="nicht im Modell">–</span>`:e.offen>0?a`<span class="zeichen warn" title=${`${e.offen} Schicht(en) nicht klassifiziert`}>⚠</span>`:e.schichten_n&&e.schichten_geprueft===e.schichten_n?a`<span class="zeichen ok" title="alle Schichten geprüft">✓</span>`:a`<span class="zeichen" title="noch zu prüfen">○</span>`}function ln(){const e=s.z.bohrungen,t=O(),n=e.filter(i=>i.entfernt);return a`
    <aside class="bohrliste-app">
      <input class="suche" type="search" placeholder="Bohrung suchen …" .value=${s.filter}
        @input=${i=>{s.filter=i.target.value,p()}}>
      <ul class="bliste" role="listbox" aria-label="Bohrungen">
        ${t.map(i=>a`
          <li role="option" aria-selected=${String(i.id===s.bid)} class=${i.id===s.bid?"aktiv":""}
            @click=${()=>ae(i.id)}>
            ${sn(i)}
            <span class="name">${i.code}</span>
            <span class="wert">${i.schichten_geprueft}/${i.schichten_n}</span>
            <button class="symbol leise-knopf" title="Aus dem Modell entfernen" aria-label=${`${i.code} entfernen`}
              @click=${r=>{r.stopPropagation(),g([{op:"entfernen",id:i.id}])}}>🗑</button>
          </li>`)}
      </ul>
      ${n.length?a`
        <details class="entfernt" ?open=${ve} @toggle=${i=>{ve=i.target.open}}>
          <summary>Entfernt / nicht im Modell (${n.length}) ${d("entfernen")}</summary>
          <ul class="bliste">
            ${n.map(i=>a`
              <li class="raus">
                <span class="name">${i.code}</span>
                <span class="wert klein">${i.doppelt_in?"doppelt":i.schichten_n?"":"ohne Schichten"}</span>
                <button class="link klein" ?disabled=${!i.schichten_n} @click=${()=>g([{op:"wiederherstellen",id:i.id}])}>wiederherstellen</button>
              </li>`)}
          </ul>
        </details>`:u}
      <p class="leise klein tasten">↑/↓ blättern · N nächste offene · G alle Schichten geprüft und weiter</p>
    </aside>`}function rn(){const e=s.z.pruefstand,[t,n]=e.bohrungen,[i,r]=e.schichten;return a`
    <div class="pruefleiste">
      <div class="balken"><span>Bohrungen geprüft <b>${t}/${n}</b></span><progress max=${n||1} value=${t}></progress></div>
      <div class="balken"><span>Schichten geprüft <b>${i}/${r}</b></span><progress max=${r||1} value=${i}></progress></div>
      <span class=${`plakette ${e.unklassifiziert_offen?"warn":"ok"}`}>
        ${e.unklassifiziert_offen?`⚠ ${e.unklassifiziert_offen} Schicht(en) nicht klassifiziert`:"✓ keine offenen Warnungen"}</span>
      ${d("warnung")}
      <span class="fueller"></span>
      ${d("pruefstand")}
      <button @click=${()=>we(!0)} ?disabled=${t===n&&i===r}>✓ Alle Bohrungen geprüft</button>
      <button class="leise-knopf" @click=${()=>we(!1)} ?disabled=${!i}>Zurücknehmen</button>
      ${d("alle_pruefen")}
    </div>`}function P(e,t,n){return a`<label class="feld"><span>${e}${n?d(n):u}</span>${t}</label>`}function on(e){const t=Ae(e.epsg,e.x,e.y);return t&&!t.ok?a`<p class="hinweise warn">⚠ ${t.text}</p>`:u}function cn(e){const t=O(),n=t.findIndex(r=>r.id===e.id),i=r=>l=>g([{op:"bohrung",id:e.id,feld:r,wert:de(l)}]);return a`
    <div class="detail-kopf">
      <div class="titelzeile">
        <h2>${e.code}</h2>
        <span class="leise">${e.dokument} · Seite ${e.seite}${e.doppelt_in?` · doppelt (auch in ${e.doppelt_in})`:""}</span>
        <span class="fueller"></span>
        <button title="Vorherige Bohrung (↑)" ?disabled=${n<=0} @click=${()=>Y(-1)}>↑ Vorherige</button>
        <button title="Nächste Bohrung (↓)" ?disabled=${n>=t.length-1} @click=${()=>Y(1)}>↓ Nächste</button>
        <button title="Nächste Bohrung mit offenen Schichten (N)" ?disabled=${!ge(n)} @click=${Fe}>⚠ Nächste offene</button>
      </div>
      <div class="felder">
        ${P("GOK [m NHN]",a`<input type="number" step="0.01" .value=${f(e.gok===null?"":String(e.gok))}
            placeholder="unbekannt" @change=${i("gok")}>
            <small class=${e.gok_quelle==="manuell"?"manuell":"leise"}>${e.gok_quelle||"fehlt"}</small>`,"gok")}
        ${P("Endteufe [m]",a`<output>${X(e.endteufe)}</output>`)}
        ${P("Rechtswert",a`<input type="number" step="0.01" .value=${f(e.x===null?"":String(e.x))} @change=${i("x")}>`,"koordinaten")}
        ${P("Hochwert",a`<input type="number" step="0.01" .value=${f(e.y===null?"":String(e.y))} @change=${i("y")}>`)}
        ${P("Koordinatensystem (EPSG)",Ke(e.epsg,r=>g([{op:"bohrung",id:e.id,feld:"epsg",wert:r}])),"epsg")}
        ${P("Ø Säule [m]",a`<input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${X(s.z.durchmesser??s.z.durchmesser_auto,1)}`}
            .value=${f(e.durchmesser===null?"":String(e.durchmesser))} @change=${i("durchmesser")}>`,"durchmesser")}
        ${P("Grundwasser",a`<output>${e.grundwasser||"–"}</output>`)}
      </div>
      ${on(e)}
      ${e.hinweise.length?a`<p class="hinweise">ℹ ${e.hinweise.join(" · ")}</p>`:u}
    </div>`}function un(e,t){const n=s.z.klassen,i=n.some(r=>r.klasse===t.bodenart);return a`
    <span class="farbfeld" style=${`background:${t.farbe}`}></span>
    <select aria-label="Bodenart" @change=${r=>g([{op:"schicht",id:e.id,k:t.k,feld:"bodenart",wert:r.target.value}])}>
      ${i?u:a`<option .selected=${!0} value=${t.bodenart}>${t.bodenart}</option>`}
      ${tn.map(([r,l])=>a`
        <optgroup label=${l}>
          ${n.filter(o=>o.art===r).map(o=>a`
            <option value=${o.klasse} .selected=${o.klasse===t.bodenart}>${o.name}${o.din4023?` (${o.din4023})`:""}</option>`)}
        </optgroup>`)}
    </select>`}function hn(e,t){return a`
    <table class="tabelle schichten">
      <thead><tr>
        <th title="geprüft">✓ ${d("geprueft")}</th><th>von [m] ${d("tiefe")}</th><th>bis [m]</th>
        <th>Bodenart ${d("bodenart")}</th><th>Beschreibung (PDF)</th><th>nach Norm ${d("norm")}</th>
      </tr></thead>
      <tbody>
        ${t.map(n=>a`
          <tr class=${[n.offen?"warn":"",n.korrigiert?"korrigiert":"",n.k===s.k?"gewaehlt":""].join(" ")}
            @click=${()=>{s.k=n.k,p()}}>
            <td><input type="checkbox" .checked=${f(n.geprueft)} aria-label="geprüft"
              @change=${i=>g([{op:"schicht",id:e.id,k:n.k,feld:"geprueft",wert:i.target.checked}],{leise:!0})}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${f(String(n.von))}
              @change=${i=>g([{op:"schicht",id:e.id,k:n.k,feld:"oben",wert:de(i)}])}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${f(String(n.bis))}
              @change=${i=>g([{op:"schicht",id:e.id,k:n.k,feld:"unten",wert:de(i)}])}></td>
            <td class="bodenart">${un(e,n)}
              ${n.offen?a`<div class="warnung">⚠ nicht klassifiziert</div>`:u}
              ${n.korrigiert?a`<div class="leise klein">korrigiert</div>`:u}</td>
            <td class="beschreibung">${n.beschreibung||a`<span class="leise">– keine Beschreibung –</span>`}
              ${n.hinweise.length?a`<div class="leise klein">${n.hinweise.join(" · ")}</div>`:u}</td>
            <td class="norm">
              ${n.norm.benennung?a`<div>${n.norm.benennung}</div>`:u}
              ${n.norm.din4023?a`<code title="Kurzzeichen nach DIN 4023">${n.norm.din4023}</code>`:u}
              ${n.norm.bodengruppe?a` <code title="Bodengruppe nach DIN 18196">${n.norm.bodengruppe}</code>`:u}
              ${[n.norm.konsistenz,n.norm.lagerung,n.norm.kalk,n.norm.bodenfarbe].filter(Boolean).length?a`<div class="leise klein">${[n.norm.konsistenz,n.norm.lagerung,n.norm.kalk,n.norm.bodenfarbe].filter(Boolean).join(" · ")}</div>`:u}
              ${n.norm.hinweise.length?a`<div class="klein hinweis-norm" title=${n.norm.hinweise.join(`
`)}>ℹ ${n.norm.hinweise[0]}${n.norm.hinweise.length>1?` (+${n.norm.hinweise.length-1})`:""}</div>`:u}
              ${n.vorschlag?a`
                <button class="vorschlag" @click=${i=>{i.stopPropagation(),g([{op:"vorschlag",id:e.id,k:n.k}])}}
                  title=${`Vorschlag nach Norm: ${n.vorschlag.benennung}${n.vorschlag.sicher?"":" (unsicher)"}`}>
                  → ${n.vorschlag.klasse} übernehmen</button>${d("vorschlag")}`:u}
            </td>
          </tr>`)}
      </tbody>
    </table>`}function dn(e,t){an(e,t);const n=Number(e.id.split(":")[0]),i=!!s.z.dokumente[n]?.pdf,r=Q?.schluessel===`${s.sig}/${n}/${(t[0]?.quelle.seite??e.seite)-1}`?Q.daten:null,l=t.find(c=>c.k===s.k)??null,o=(c,v)=>{if(!c||!r)return u;const w=r.px_je_pt*_;return a`<div class=${`bbox ${v}`} style=${`left:${c[0]*w}px;top:${c[1]*w}px;width:${(c[2]-c[0])*w}px;height:${(c[3]-c[1])*w}px`}></div>`},h=t.map(c=>c.quelle.bbox).filter(c=>!!c&&c.length===4),b=h.length?[Math.min(...h.map(c=>c[0])),Math.min(...h.map(c=>c[1])),Math.max(...h.map(c=>c[2])),Math.max(...h.map(c=>c[3]))]:null;return a`
    <aside class="quelle-spalte">
      <div class="saeule-rahmen">
        ${en(t.map(c=>({k:c.k,von:c.von,bis:c.bis,farbe:c.farbe,warn:c.offen,geprueft:c.geprueft,titel:`${X(c.von)}–${X(c.bis)} m: ${c.bodenart}${c.beschreibung?` – ${c.beschreibung}`:""}`})),{hoehe:420,gewaehlt:s.k,waehlen:c=>{s.k=c,p()}})}
      </div>
      ${i?a`<div class="pdf-rahmen">
        <div class="pdf-kopf"><b>Quelle im PDF</b> ${d("quelle")}
          <span class="fueller"></span>
          ${i?a`<button class="symbol" title="kleiner" @click=${()=>{_=Math.max(.25,_/1.4),p()}}>−</button>
            <button class="symbol" title="größer" @click=${()=>{_=Math.min(1.5,_*1.4),p()}}>+</button>`:u}
        </div>
        ${r?a`
          ${gn(b,r.px_je_pt*_)}
          <div class="pdf-seite">
            <div class="pdf-flaeche" style=${`width:${r.breite_pt*r.px_je_pt*_}px;height:${r.hoehe_pt*r.px_je_pt*_}px`}>
              <img src=${r.url} alt=${`Seite ${r.seite+1}`} draggable="false">
              ${o(b,"saeule-bbox")}
              ${o(l?.quelle.bbox,"schicht-bbox")}
            </div>
          </div>`:a`<p class="leise klein">Seite wird geladen …</p>`}
      </div>`:u}
    </aside>`}let ze="";function gn(e,t){const n=`${s.bid}/${_}`;return!e||ze===n?u:(requestAnimationFrame(()=>{const i=document.querySelector(".pdf-seite");i&&(i.scrollLeft=Math.max(0,e[0]*t-i.clientWidth/3),i.scrollTop=Math.max(0,e[1]*t-40),ze=n)}),u)}function pn(){const e=s.z,t=s.details.get(s.bid),n=e.bohrungen.find(l=>l.id===s.bid),i=n?Number(n.id.split(":")[0]):0,r=!e.dokumente[i]?.pdf;return a`
    <div class=${`schritt-bohrungen ${r?"ohne-pdf":""}`}>
      ${rn()}
      ${ln()}
      <section class="bohrung-detail">
        ${n?a`
          ${cn(n)}
          ${t?a`
            ${hn(n,t.schichten)}
            <div class="detail-fuss">
              <button class="primaer" title="Alle Schichten dieser Bohrung als geprüft markieren und zur nächsten offenen (G)"
                @click=${He}>✓ Alle Schichten geprüft – weiter</button>
              <button class="leise-knopf" ?disabled=${!n.schichten_geprueft}
                @click=${()=>g([{op:"bohrung_pruefen",id:n.id,wert:!1}])}>Prüfung zurücknehmen</button>
              <span class="fueller"></span>
              <button class="gefahr" @click=${()=>g([{op:"entfernen",id:n.id}])}>🗑 Aus dem Modell entfernen</button>
            </div>`:a`<p class="leise">Schichten werden geladen …</p>`}`:a`<p class="leise">Links eine Bohrung wählen.</p>`}
      </section>
      ${n&&t?dn(n,t.schichten):a`<aside class="quelle-spalte"></aside>`}
    </div>`}const ee=(e,t=2)=>e==null||!Number.isFinite(e)?"":e.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),x=e=>{const t=e.target.value.trim().replace(",",".");return t===""?null:Number(t)};let $=null,ne="",H="plan";function Se(e){const t=e.unterlage;return t?`${t.sha}/${t.seite}/${t.art}/${JSON.stringify(t.kalibrierung)}`:""}function Re(e){const t=e.unterlage;if(!t)return $=null;if($&&$.schluessel===Se(e))return $;const n=t.kalibrierung,i=o=>o&&!("n"in o)?o:null,r=i(n?.massstab),l=i(n?.hoehe);return $={schluessel:Se(e),massArt:n?.massstab&&"n"in n.massstab?"n":"strecke",p1:r?{u:r.u1,v:r.v1}:null,p2:r?{u:r.u2,v:r.v2}:null,meter:r?.meter??null,n:n?.massstab&&"n"in n.massstab?n.massstab.n:null,hoeheArt:n?.hoehe?"n"in n.hoehe?"n":"strecke":"gleich",h1:l?{u:l.u1,v:l.v1}:null,h2:l?{u:l.u2,v:l.v2}:null,hoeheMeter:l?.meter??null,hoeheN:n?.hoehe&&"n"in n.hoehe?n.hoehe.n:null,bezug:n?.bezug?{u:n.bezug.u,v:n.bezug.v}:null,x:n?.bezug?.x??null,y:n?.bezug?.y??null,drehung:n?.drehung??0,epsg:n?.epsg??e.viewer.epsg??null},$}function $e(e,t=!1){const n=$,i=e.unterlage;if(!n||!i)return null;let r=null;if(n.massArt==="n"&&n.n&&n.n>0&&(r={n:n.n}),n.massArt==="strecke"&&n.p1&&n.p2&&n.meter&&n.meter>0&&(r={u1:n.p1.u,v1:n.p1.v,u2:n.p2.u,v2:n.p2.v,meter:n.meter}),!r||!n.bezug||n.x===null||n.y===null)return null;let l=null;return i.art==="schnitt"&&n.hoeheArt==="n"&&n.hoeheN&&n.hoeheN>0&&(l={n:n.hoeheN}),i.art==="schnitt"&&n.hoeheArt==="strecke"&&n.h1&&n.h2&&n.hoeheMeter&&n.hoeheMeter>0&&(l={u1:n.h1.u,v1:n.h1.v,u2:n.h2.u,v2:n.h2.v,meter:n.hoeheMeter}),{massstab:r,hoehe:l,bezug:{...n.bezug,x:n.x,y:n.y},drehung:i.art==="plan"?n.drehung:0,epsg:i.art==="plan"?n.epsg:null,gesperrt:t}}function k(){const e=s.z;s.entwurf=$e(e);const t=s.viewer;t&&$&&(t.editor.hilfsmarken({strecke:$.massArt==="strecke"?[$.p1,$.p2]:[],hoehe:$.hoeheArt==="strecke"?[$.h1,$.h2]:[],bezug:$.bezug}),s.entwurf&&t.editor.vorschau(s.entwurf)),p()}async function mn(e){const t=s.viewer;if(!t||!$)return;ne=e,p();const n=await t.editor.bildpunktWaehlen();if(ne="",!n||!$||s.z?.unterlage?.kalibrierung?.gesperrt){p();return}$[e]=n,k()}async function ye(e){s.viewer?.editor.waehlenAbbrechen();const t=$e(s.z,e);if(!t){T("Für die Kalibrierung fehlen Maßstab oder Bezugspunkt.","warn");return}await g([{op:"kalibrierung",wert:t}])&&(s.entwurf=null,T(e?"Plan kalibriert und gesperrt – jetzt die Bohrungen ziehen.":"Kalibrierung übernommen.","ok"),await s.viewer?.ansicht(s.z?.unterlage?.art==="schnitt"?"sued":"oben"))}async function $n(e){const t=s.z.unterlage;t?.kalibrierung&&await g([{op:"kalibrierung",wert:{...t.kalibrierung,gesperrt:e}}])}async function fn(e){const t=e.target,n=t.files?.[0];if(t.value="",!n)return;const i=await B(()=>y.unterlage(s.sig,n,H,0),"Unterlage wird gelesen …");i&&(se(i),s.entwurf=null,p(),await pe(),await s.viewer?.lageModus(!0),await s.viewer?.ansicht(i.unterlage?.art==="schnitt"?"sued":"oben"))}async function xe(e,t){const n=await B(()=>y.unterlageSeite(s.sig,e,t),"Seite wird gelesen …");n&&(se(n),s.entwurf=null,p(),await pe(),await s.viewer?.ansicht(t==="schnitt"?"sued":"oben"))}async function bn(){if(!confirm("Unterlage mit ihrer Kalibrierung entfernen? Gesetzte Bohrungen behalten ihre Lage."))return;const e=await B(()=>y.unterlageEntfernen(s.sig));e&&(se(e),s.entwurf=null,p(),await pe())}const G=(e,t,n=!0)=>a`<details class="abschnitt" ?open=${n}><summary>${e}</summary><div class="abschnitt-inhalt">${t}</div></details>`;function F(e,t,n,i){return a`<button class=${`punkt ${ne===t?"aktiv":""} ${n?"gesetzt":""}`} ?disabled=${i}
    @click=${()=>mn(t)}>${ne===t?"… im Plan klicken":n?`${e} ✓`:e}</button>`}function kn(e){const t=Ae(e.epsg,e.x,e.y);return t?a`<p class=${`klein ${t.ok?"ok":"warn"}`}>${t.ok?"✓":"⚠"} ${t.text}</p>`:u}function vn(e){const t=e.unterlage,n=Re(e),i=!!t.kalibrierung?.gesperrt,r=t.art==="plan",l=n.p1&&n.p2?Math.hypot(n.p2.u-n.p1.u,n.p2.v-n.p1.v):null,o=$e(e),h=o?Oe(o.massstab,t.mm_pro_px):null,b=e.viewer.bohrungen.filter(c=>c.x!==null&&(r?!/Plan|Viewer/.test(c.quelle):c.gok_bekannt));return a`
    <p class=${`status ${t.kalibrierung?i?"ok":"":"warn"}`}>
      ${t.kalibrierung?a`${i?"🔒 gesperrt · ":""}${be(t)}${r?` · ${De(t.kalibrierung.epsg)}`:""}`:"nicht kalibriert"}
      ${s.entwurf&&JSON.stringify({...s.entwurf,gesperrt:!1})!==JSON.stringify({...t.kalibrierung??{},gesperrt:!1})?a`<br><span class="leise">Vorschau: ${be(t,s.entwurf)} (noch nicht übernommen)</span>`:u}
    </p>
    ${i?a`
      <p class="leise klein">Der Plan liegt fest. ${r?"Bohrungen unten mit „Punkte setzen“ in den Plan klicken oder im Viewer ziehen – nur in x/y":"Bohrungen im Viewer ziehen – entlang der Station; die Höhe nur ohne GOK aus dem PDF"}.</p>
      <button @click=${()=>$n(!1)}>🔓 Entsperren (neu kalibrieren)</button>`:a`
      <fieldset class="gruppe">
        <legend>1 · Maßstab ${d("massstab")}</legend>
        <div class="umschalter">
          <label><input type="radio" name="massart" .checked=${n.massArt==="strecke"} @change=${()=>{n.massArt="strecke",k()}}> Strecke messen</label>
          <label><input type="radio" name="massart" .checked=${n.massArt==="n"} @change=${()=>{n.massArt="n",k()}}> 1:n eingeben</label>
        </div>
        ${n.massArt==="strecke"?a`
          <div class="zeile">${F("Punkt 1","p1",n.p1,!1)}${F("Punkt 2","p2",n.p2,!1)}</div>
          <div class="zeile">
            <span class="leise klein">${l?`gemessen ${ee(l,0)} px`:"zwei Punkte anklicken"}</span>
            <label class="inline">wahre Länge <input type="number" step="0.01" min="0" class="kurz" .value=${f(n.meter===null?"":String(n.meter))}
              @input=${c=>{n.meter=x(c),k()}}> m</label>
          </div>`:a`
          <label class="inline">Maßstab 1: <input type="number" step="1" min="1" class="kurz" .value=${f(n.n===null?"":String(n.n))}
            @input=${c=>{n.n=x(c),k()}}></label>`}
        ${h?a`<p class="leise klein">ergibt 1:${Math.round(h).toLocaleString("de-DE")}</p>`:u}
      </fieldset>
      ${r?u:a`
        <fieldset class="gruppe">
          <legend>Höhenmaßstab ${d("hoehe")}</legend>
          <div class="umschalter">
            <label><input type="radio" name="hoeheart" .checked=${n.hoeheArt==="gleich"} @change=${()=>{n.hoeheArt="gleich",k()}}> wie Länge</label>
            <label><input type="radio" name="hoeheart" .checked=${n.hoeheArt==="n"} @change=${()=>{n.hoeheArt="n",k()}}> 1:n</label>
            <label><input type="radio" name="hoeheart" .checked=${n.hoeheArt==="strecke"} @change=${()=>{n.hoeheArt="strecke",k()}}> messen</label>
          </div>
          ${n.hoeheArt==="n"?a`<label class="inline">Höhe 1: <input type="number" step="1" min="1" class="kurz"
              .value=${f(n.hoeheN===null?"":String(n.hoeheN))} @input=${c=>{n.hoeheN=x(c),k()}}></label>`:u}
          ${n.hoeheArt==="strecke"?a`
            <div class="zeile">${F("Höhe oben","h1",n.h1,!1)}${F("Höhe unten","h2",n.h2,!1)}</div>
            <label class="inline">Höhenunterschied <input type="number" step="0.01" min="0" class="kurz"
              .value=${f(n.hoeheMeter===null?"":String(n.hoeheMeter))} @input=${c=>{n.hoeheMeter=x(c),k()}}> m</label>`:u}
        </fieldset>`}
      <fieldset class="gruppe">
        <legend>2 · Bezugspunkt ${d("bezug")}</legend>
        <div class="zeile">${F("Punkt im Plan wählen","bezug",n.bezug,!1)}</div>
        <div class="zeile">
          <label class="feld schmal"><span>${r?"Rechtswert":"Station [m]"}</span>
            <input type="number" step="0.01" .value=${f(n.x===null?"":String(n.x))} @input=${c=>{n.x=x(c),k()}}></label>
          <label class="feld schmal"><span>${r?"Hochwert":"Höhe [m NHN]"}</span>
            <input type="number" step="0.01" .value=${f(n.y===null?"":String(n.y))} @input=${c=>{n.y=x(c),k()}}></label>
        </div>
        ${r?a`
          <label class="feld breit"><span>Koordinatensystem (EPSG) ${d("epsg")}</span>
            ${Ke(n.epsg,c=>{n.epsg=c,k()})}</label>
          ${kn(n)}`:u}
        ${b.length?a`
          <label class="inline klein">oder von Bohrung
            <select @change=${c=>{const v=e.viewer.bohrungen.find(w=>w.id===c.target.value);v&&(n.x=v.x,n.y=r?v.y:v.gok,k())}}>
              <option value="">–</option>
              ${b.map(c=>a`<option value=${c.id}>${c.code}</option>`)}
            </select></label>`:u}
      </fieldset>
      ${r?a`
        <fieldset class="gruppe">
          <legend>3 · Drehung ${d("drehung")}</legend>
          <div class="zeile">
            <label class="inline"><input type="number" step="0.1" class="kurz" .value=${f(String(n.drehung))}
              @input=${c=>{n.drehung=x(c)??0,k()}}> ° gegen den Uhrzeigersinn</label>
          </div>
        </fieldset>`:u}
      <div class="zeile knopfzeile">
        <button ?disabled=${!o} @click=${()=>ye(!1)}>Übernehmen</button>
        <button class="primaer" ?disabled=${!o} @click=${()=>ye(!0)}>🔒 Übernehmen und sperren</button>
        ${d("sperren")}
      </div>
      ${t.kalibrierung?a`<button class="link klein" @click=${()=>g([{op:"kalibrierung",wert:null}])}>Kalibrierung zurücksetzen</button>`:u}`}`}function wn(e){const t=e.unterlage;return t?a`
    <p><b>${t.name}</b> <span class="leise">· ${t.art==="plan"?"Lageplan":"Längsschnitt"}</span></p>
    <div class="zeile">
      ${(t.seiten??1)>1?a`<label class="inline">Seite <select @change=${n=>xe(Number(n.target.value),t.art)}>
          ${Array.from({length:t.seiten},(n,i)=>a`<option value=${i} .selected=${i===t.seite}>${i+1}</option>`)}
        </select></label>`:u}
      <label class="inline">Ansicht <select @change=${n=>xe(t.seite,n.target.value)}>
        <option value="plan" .selected=${t.art==="plan"}>Lageplan</option>
        <option value="schnitt" .selected=${t.art==="schnitt"}>Längsschnitt</option>
      </select></label>
    </div>
    <label class="inline">Deckkraft ${d("deckkraft")}
      <input type="range" min="0.1" max="1" step="0.05" .value=${String(s.viewer?.editor.deckkraft??.85)}
        @input=${n=>{s.viewer&&(s.viewer.editor.deckkraft=Number(n.target.value),s.viewer.editor.bildSichtbarkeit())}}></label>
    <button class="link klein" @click=${bn}>Unterlage entfernen</button>`:a`
      <p class="leise klein">Lageplan (von oben) oder Längsschnitt (von der Seite) als PDF – er liegt im Viewer unter den Bohrungen.</p>
      <div class="umschalter">
        <label><input type="radio" name="neueart" .checked=${H==="plan"} @change=${()=>{H="plan"}}> Lageplan</label>
        <label><input type="radio" name="neueart" .checked=${H==="schnitt"} @change=${()=>{H="schnitt"}}> Längsschnitt</label>
      </div>
      <label class="datei-knopf"><input type="file" accept=".pdf,application/pdf" @change=${fn}>PDF wählen …</label>`}function zn(e){const t=e.unterlage,n=!t||!!t.kalibrierung?.gesperrt,i=e.viewer.bohrungen.filter(o=>o.x===null),r=e.lage_modus==="reihe",l=!r&&t?.art==="plan"&&!!t.kalibrierung?.gesperrt;return a`
    ${n?u:a`<p class="warnung">Erst kalibrieren und sperren (🔒) – dann Punkte setzen oder Bohrungen ziehen.</p>`}
    ${l?Sn(e):u}
    ${i.length?a`
      <p class="klein">Ohne Lage (${i.length}) – ${l?"anklicken = als Nächste setzen, oder":""} in den Viewer ziehen
        ${d("ohne_lage")}</p>
      <div class="parkplatz">
        ${i.map(o=>a`<span class=${`park ${n?"":"gesperrt"} ${s.punktModus&&s.naechste===o.id?"aktiv":""}`}
          title=${l?"Klick: als nächste Bohrung setzen · Ziehen: direkt in den Viewer":"In den Viewer ziehen"}
          @pointerdown=${h=>s.viewer?.editor.ziehenStart(h,o.id,!0)}
          @click=${()=>{l&&te(!0,o.id)}}>${o.code}</span>`)}
      </div>`:a`<p class="leise klein">Alle Bohrungen im Modell haben eine Lage.</p>`}
    ${l?yn(e):u}
    ${r?xn(e):u}`}function te(e,t){s.punktModus=e,t!==void 0?s.naechste=t:e&&!s.naechste&&(s.naechste=We()),s.viewer?.editor.punktModusSetzen(e),p()}function Sn(e){const t=e.viewer.bohrungen.filter(i=>i.x===null),n=e.viewer.bohrungen.filter(i=>i.x!==null);return a`
    <div class="zeile">
      <button class=${s.punktModus?"primaer":""} @click=${()=>te(!s.punktModus)}>
        ${s.punktModus?"● Punkte setzen – Klick in den Plan":"＋ Punkte im Plan setzen"}</button>
      ${s.punktModus?a`<button class="leise-knopf" @click=${()=>te(!1)}>Fertig (Esc)</button>`:u}
      ${d("punkte")}
    </div>
    ${s.punktModus?a`
      <label class="feld breit"><span>Nächster Klick setzt</span>
        <select class="naechste" @change=${i=>{s.naechste=i.target.value,p()}}>
          <option value="" .selected=${!s.naechste}>– freien Punkt (später zuordnen) –</option>
          ${t.length?a`<optgroup label="Ohne Lage">
            ${t.map(i=>a`<option value=${i.id} .selected=${s.naechste===i.id}>${i.code}</option>`)}</optgroup>`:u}
          ${n.length?a`<optgroup label="Mit Lage (neu setzen)">
            ${n.map(i=>a`<option value=${i.id} .selected=${s.naechste===i.id}>${i.code}</option>`)}</optgroup>`:u}
        </select></label>
      <p class="leise klein">Danach ist automatisch die nächste Bohrung ohne Lage dran.</p>`:u}`}function yn(e){const t=e.viewer.bohrungen.filter(l=>l.x!==null&&/Plan|Viewer/.test(l.quelle)),n=e.viewer.bohrungen,i=n.filter(l=>l.x===null);if(!t.length&&!e.punkte.length)return u;const r=(l,o)=>a`<span class="leise klein">R ${ee(l)}<br>H ${ee(o)}</span>`;return a`
    <p class="klein">Gesetzte Punkte (${t.length+e.punkte.length})</p>
    <table class="tabelle kompakt punkte">
      <tbody>
        ${e.punkte.map(l=>a`
          <tr class=${`frei ${s.viewer?.editor.punktGewaehlt===l.id?"gewaehlt":""}`}>
            <td><button class="link" title="Im Viewer wählen" @click=${()=>{s.viewer?.editor.punktWaehlen(l.id),p()}}>◆ ${l.id}</button></td>
            <td>${r(l.x,l.y)}</td>
            <td><select aria-label=${`${l.id} zuordnen`} @change=${o=>{const h=o.target.value;h&&g([{op:"punkt_zuordnen",punkt:l.id,bohrung:h}])}}>
              <option value="" selected>– Bohrung zuordnen –</option>
              ${i.length?a`<optgroup label="Ohne Lage">${i.map(o=>a`<option value=${o.id}>${o.code}</option>`)}</optgroup>`:u}
              <optgroup label="Mit Lage (ersetzen)">${n.filter(o=>o.x!==null).map(o=>a`<option value=${o.id}>${o.code}</option>`)}</optgroup>
            </select></td>
            <td><button class="symbol" title="Punkt löschen" @click=${()=>g([{op:"punkt_loeschen",punkt:l.id}])}>✕</button></td>
          </tr>`)}
        ${t.map(l=>a`
          <tr class=${s.viewer?.editor.ausgewaehlt===l.id?"gewaehlt":""}>
            <td><button class="link" title="Im Viewer wählen" @click=${()=>{s.viewer?.nadelWaehlen(l.id),p()}}>● ${l.code}</button></td>
            <td>${r(l.x,l.y)}</td>
            <td><select aria-label=${`${l.code} umhängen`} @change=${o=>{const h=o.target.value;h==="-"?g([{op:"lage_loesen",id:l.id}]):h&&h!==l.id&&g([{op:"lage_umhaengen",id:l.id,nach:h}])}}>
              <option value=${l.id} selected>${l.code}</option>
              <option value="-">– Zuordnung lösen (freier Punkt) –</option>
              ${i.length?a`<optgroup label="Andere Bohrung (ohne Lage)">${i.map(o=>a`<option value=${o.id}>${o.code}</option>`)}</optgroup>`:u}
            </select></td>
            <td><button class="symbol" title="Lage entfernen (Bohrung wieder ohne Lage)" @click=${()=>g([{op:"lage_entfernen",id:l.id}])}>✕</button></td>
          </tr>`)}
      </tbody>
    </table>`}function xn(e){const t=e.reihe.map(i=>i.id),n=(i,r)=>{const l=[...t],[o]=l.splice(i,1);l.splice(Math.max(0,Math.min(l.length,i+r)),0,o),g([{op:"reihe",reihenfolge:l}],{leise:!0})};return a`
    <div class="zeile">
      <label class="inline">Standardabstand ${d("standardabstand")}
        <input type="number" step="1" min="1" class="kurz" .value=${f(String(e.reihe_standard))}
          @change=${i=>g([{op:"reihe",standard:x(i)}])}> m</label>
    </div>
    <table class="tabelle kompakt reihe">
      <thead><tr><th></th><th>Bohrung</th><th>Abstand [m] ${d("reihe")}</th><th>Station [m]</th></tr></thead>
      <tbody>
        ${e.reihe.map((i,r)=>a`
          <tr>
            <td class="pfeile"><button class="symbol" ?disabled=${r===0} title="nach vorn" @click=${()=>n(r,-1)}>▲</button><button class="symbol"
              ?disabled=${r===t.length-1} title="nach hinten" @click=${()=>n(r,1)}>▼</button></td>
            <td>${i.code}</td>
            <td><input type="number" step="0.1" min="0" class="kurz" ?disabled=${r===0} .value=${f(i.abstand===null?"":String(i.abstand))}
              @change=${l=>g([{op:"reihe",abstand:{[i.id]:x(l)}}],{leise:!0})}></td>
            <td><input type="number" step="0.1" class="kurz" .value=${f(String(i.station))} title=${i.quelle_text}
              @change=${l=>g([{op:"reihe",station:{[i.id]:x(l)}}],{leise:!0})}></td>
          </tr>`)}
      </tbody>
    </table>`}function Bn(e){const t=s.viewer;t&&(!e.unterlage||e.unterlage.kalibrierung?.gesperrt||!$?t.editor.hilfsmarken({}):t.editor.hilfsmarken({strecke:$.massArt==="strecke"?[$.p1,$.p2]:[],hoehe:$.hoeheArt==="strecke"?[$.h1,$.h2]:[],bezug:$.bezug}))}let Be=!1;function Mn(){const e=s.z;Re(e),Bn(e);const t=e.lage_modus!=="reihe"&&e.unterlage?.art==="plan"&&!!e.unterlage.kalibrierung?.gesperrt;return s.punktModus&&!t&&(s.punktModus=!1),s.viewer?.editor.punktModusSetzen(s.punktModus),Be||(Be=!0,window.addEventListener("keydown",n=>{n.key==="Escape"&&s.schritt==="lage"&&s.punktModus&&te(!1)})),a`
    <div class="app-panel links">
      ${G(a`Lage der Bohrungen ${d("lage_art")}`,a`
        <div class="umschalter">
          <label><input type="radio" name="lagemodus" .checked=${e.lage_modus==="koordinaten"}
            @change=${()=>g([{op:"lage_modus",wert:"koordinaten"}])}> Koordinaten (Lageplan)</label>
          <label><input type="radio" name="lagemodus" .checked=${e.lage_modus==="reihe"}
            @change=${()=>g([{op:"lage_modus",wert:"reihe"}])}> Reihe (Längsschnitt)</label>
        </div>`)}
      ${G(a`Unterlage ${d("unterlage")}`,wn(e))}
      ${e.unterlage?G(a`Kalibrieren`,vn(e)):u}
      ${G(a`Bohrungen setzen`,zn(e))}
      ${G(a`Darstellung`,a`
        <label class="inline">Ø Bohrsäulen ${d("durchmesser")}
          <input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${ee(e.durchmesser_auto,1)}`}
            .value=${f(e.durchmesser===null?"":String(e.durchmesser))}
            @change=${n=>g([{op:"durchmesser",wert:x(n)}])}> m</label>
        <p class="leise klein">Je Bohrung im Schritt Bohrungen (Ø Säule). Leer = automatisch nach Modellgröße.</p>`,!1)}
      ${e.hinweise.length?a`<div class="hinweisliste">${e.hinweise.map(n=>a`<p class="klein">ℹ ${n}</p>`)}</div>`:u}
    </div>`}const D=(e,t=1)=>e==null?"–":e.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});let A="",oe=null,Me="";function _n(){const e=s.z.einstellungen,t=(r,l)=>g([{op:"einstellungen",[r]:l}]),n=(r,l,o,h,b)=>{const c=e[r];return a`
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${c===null} @change=${v=>t(r,v.target.checked?null:h)}> ${l} automatisch</label>${d(b)}
        ${c===null?u:a`<input type="number" step="any" class="kurz" .value=${f(String(c))}
          @change=${v=>t(r,Number(v.target.value))}> ${o}`}
      </div>`},i=s.modell?.bericht?.parameter??{};return a`
    <section class="karte">
      <h3>Modell</h3>
      <div class="einstellung">
        <span>Interpolation ${d("methode")}</span>
        <label class="inline"><input type="radio" name="methode" .checked=${e.methode==="idw"} @change=${()=>t("methode","idw")}> IDW</label>
        <label class="inline"><input type="radio" name="methode" .checked=${e.methode==="tps"} @change=${()=>t("methode","tps")}> Dünnplatten-Spline</label>
      </div>
      ${n("puffer","Puffer","m",Number(i.puffer_m??20),"puffer")}
      ${n("raster","Raster","m",Number(i.raster_m??5),"raster")}
      ${n("basis","Modellbasis","m NHN",Math.floor(Number(i.basis_nhn??0)),"basis")}
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${e.gok_relativ} @change=${r=>t("gok_relativ",r.target.checked)}> fehlende GOK: Gelände = 0 m</label>${d("gok_relativ")}
      </div>
      ${i.raster_m!==void 0?a`<p class="leise klein">gerechnet: Puffer ${D(Number(i.puffer_m),0)} m · Raster ${D(Number(i.raster_m))} m ·
        Basis ${D(Number(i.basis_nhn),2)} m NHN · Fläche ${D(Number(i.flaeche_m2)/1e4,2)} ha</p>`:u}
    </section>`}function Nn(){const e=s.modell?.bericht;if(!e)return u;const t=s.z.vorgabe??e.vorlage_einheiten,n=JSON.stringify(t);(!oe||Me!==n)&&(oe=t.map(l=>({name:l.name,bodenarten:l.bodenarten.join(", ")})),Me=n);const i=oe,r=()=>g([{op:"vorgabe",wert:i.filter(l=>l.name.trim()).map(l=>({name:l.name.trim(),bodenarten:l.bodenarten.split(",").map(o=>o.trim()).filter(Boolean)}))}]);return a`
    <section class="karte">
      <h3>Einheiten festlegen ${d("einheiten")}</h3>
      <p class="leise klein">${s.z.vorgabe?"Vorgegeben (eigene Einheiten).":"Automatisch korreliert – hier umbenennen oder Bodenarten zusammenlegen."}</p>
      <table class="tabelle kompakt vorgabe">
        <colgroup><col class="pfeil"><col><col><col class="weg"></colgroup>
        <thead><tr><th></th><th>Einheit</th><th>Bodenarten (mit Komma)</th><th></th></tr></thead>
        <tbody>
          ${i.map((l,o)=>a`
            <tr>
              <td class="pfeile"><button class="symbol" ?disabled=${o===0} @click=${()=>{i.splice(o-1,0,...i.splice(o,1)),p()}}>▲</button><button
                class="symbol" ?disabled=${o===i.length-1} @click=${()=>{i.splice(o+1,0,...i.splice(o,1)),p()}}>▼</button></td>
              <td><input .value=${f(l.name)} @input=${h=>{l.name=h.target.value}}></td>
              <td><input .value=${f(l.bodenarten)} @input=${h=>{l.bodenarten=h.target.value}}></td>
              <td><button class="symbol" title="Zeile löschen" @click=${()=>{i.splice(o,1),p()}}>✕</button></td>
            </tr>`)}
        </tbody>
      </table>
      <div class="zeile knopfzeile">
        <button class="link" @click=${()=>{i.push({name:"",bodenarten:""}),p()}}>+ Zeile</button>
        <span class="fueller"></span>
        <button ?disabled=${!s.z.vorgabe} @click=${()=>g([{op:"vorgabe",wert:null}])}>Automatisch korrelieren</button>
        <button class="primaer" @click=${r}>Mit diesen Einheiten rechnen</button>
      </div>
    </section>`}function Pn(){const e=s.modell,t=e?.bericht,n=t?.einheiten.find(i=>i.name===A);return a`
    <div class="schritt-einheiten">
      <div class="spalte">
        ${_n()}
        ${Nn()}
      </div>
      <div class="spalte breit">
        ${s.rechnet?a`<div class="karte"><div class="kreisel klein"></div> Modell wird gerechnet …</div>`:u}
        ${e?.fehler?a`<div class="karte warnung">Noch kein Modell: ${e.fehler}
          <button class="link" @click=${()=>N("lage")}>→ Lage setzen</button></div>`:u}
        ${t?a`
          <section class="karte">
            <h3>Einheiten (${t.einheiten.length})</h3>
            <table class="tabelle einheiten">
              <thead><tr><th></th><th>Einheit</th><th>Bodenarten</th><th>Volumen [m³]</th><th>max. Mächtigkeit [m]</th>
                <th title="in Bohrungen vorhanden / fehlt / unter der Endteufe">✓ / – / ?</th><th>Hinweise</th></tr></thead>
              <tbody>
                ${t.einheiten.map(i=>a`
                  <tr class=${i.name===A?"gewaehlt":""} @click=${()=>{A=A===i.name?"":i.name,p()}}>
                    <td><span class="farbfeld" style=${`background:${i.farbe}`}></span></td>
                    <td><b>${i.name}</b></td>
                    <td>${i.bodenarten.join(", ")}</td>
                    <td class="zahl">${Math.round(i.volumen_m3).toLocaleString("de-DE")}</td>
                    <td class="zahl">${D(i.maechtigkeit_max_m,2)}</td>
                    <td class="zahl">${i.bohrungen.vorhanden.length} / ${i.bohrungen.fehlt.length} / ${i.bohrungen.unbekannt.length}</td>
                    <td class="klein">${i.hinweise.join("; ")}</td>
                  </tr>`)}
              </tbody>
            </table>
          </section>
          <section class="karte profil-karte">
            <h3>Einheiten je Bohrung <span class="leise klein">(m NHN, Klick wählt die Einheit)</span></h3>
            <div class="profil-scroll">${nn(t,{hoehe:380,gewaehlt:A,waehlen:i=>{A=i,p()}})}</div>
          </section>
          ${n?a`
            <section class="karte">
              <h3><span class="farbfeld" style=${`background:${n.farbe}`}></span> ${n.name}: Beschreibungen aus dem PDF</h3>
              <table class="tabelle kompakt">
                <thead><tr><th>Bohrung</th><th>Tiefe [m]</th><th>Bodenart</th><th>Beschreibung</th></tr></thead>
                <tbody>${n.schichten.map(i=>a`
                  <tr><td>${i.bohrung}</td><td class="zahl">${D(i.von,2)}–${D(i.bis,2)}</td><td>${i.bodenart??"unklassifiziert"}</td>
                    <td>${i.beschreibung||a`<span class="leise">–</span>`}</td></tr>`)}</tbody>
              </table>
            </section>`:u}`:u}
      </div>
    </div>`}let ie="";async function En(){const e=await B(()=>y.einchecken(s.sig,ie));e&&(se(e.zustand),ie="",T(`Eingecheckt: v${e.eintrag.nr} · ${e.eintrag.stand.bohrungen[0]}/${e.eintrag.stand.bohrungen[1]} Bohrungen geprüft`,"ok"),p())}function Dn(){const e=s.z,t=s.modell,n=t?.bericht,i=e.pruefstand,r=e.eincheckungen[e.eincheckungen.length-1],l=[["ifc","Baugrundmodell (IFC 4.3)"],["bericht","Prüfbericht (JSON)"],["einheiten","Einheiten-Vorlage (JSON)"],["extraktion","Extraktion (JSON)"],["eingabe","Modell-Eingabe mit Korrekturen (JSON)"],["projekt","Projektstand (JSON)"]];return a`
    <div class="app-panel rechts">
      <section class="abschnitt-flach">
        <h3>Modell</h3>
        ${s.rechnet?a`<p><span class="kreisel klein"></span> wird gerechnet …</p>`:u}
        ${t?.fehler?a`<p class="warnung">Noch kein Modell: ${t.fehler}</p>
          <button class="link" @click=${()=>N("lage")}>→ Lage setzen</button>`:u}
        ${n?a`
          <ul class="kennzahlen">
            <li><b>${n.einheiten.length}</b> Einheiten</li>
            <li><b>${n.bohrungen.length}</b> Bohrungen im Modell</li>
            <li class=${n.epsg?"":"warn"}>${n.epsg?`EPSG:${n.epsg}`:"lokales System"}</li>
            <li class=${n.pruefungen.alle_koerper_geschlossen?"ok":"warn"}>${n.pruefungen.alle_koerper_geschlossen?"Körper geschlossen":"Körper offen"}</li>
            <li class=${n.pruefungen.max_abweichung_an_bohrungen_m<.01?"ok":"warn"}>Abweichung an Bohrungen ${n.pruefungen.max_abweichung_an_bohrungen_m.toFixed(3)} m</li>
          </ul>`:u}
        <div class="zeile">
          <label class="inline"><input type="checkbox" .checked=${e.auto} @change=${o=>g([{op:"auto",wert:o.target.checked}],{leise:!0})}>
            automatisch nachführen</label>${d("auto")}
          <span class="fueller"></span>
          <button ?disabled=${s.rechnet} @click=${()=>Ve()}>Neu rechnen</button>
        </div>
        <label class="inline">Überhöhung ${d("ueberhoehung")}
          <select @change=${async o=>{const h=Number(o.target.value);await s.viewer?.ueberhoehen(h),await g([{op:"ueberhoehung",wert:h}],{leise:!0})}}>
            ${[1,2,5,10,20].map(o=>a`<option value=${o} .selected=${e.ueberhoehung===o}>${o}×</option>`)}
          </select></label>
      </section>

      <section class="abschnitt-flach">
        <h3>Prüfstand ${d("pruefstand")}</h3>
        <div class="balken"><span>Bohrungen <b>${i.bohrungen[0]}/${i.bohrungen[1]}</b></span><progress max=${i.bohrungen[1]||1} value=${i.bohrungen[0]}></progress></div>
        <div class="balken"><span>Schichten <b>${i.schichten[0]}/${i.schichten[1]}</b></span><progress max=${i.schichten[1]||1} value=${i.schichten[0]}></progress></div>
        <p class="klein">${i.unklassifiziert_offen?a`<span class="warnung">⚠ ${i.unklassifiziert_offen} Schicht(en) nicht klassifiziert</span>
          <button class="link" @click=${()=>N("bohrungen")}>prüfen</button>`:a`<span class="ok">✓ keine offenen Warnungen</span>`}
          · ${i.korrigiert} korrigiert · ${i.manuelle_lage} Lagen manuell · ${i.entfernt} entfernt</p>
        <p class=${`klein ${r&&!e.seit_einchecken_geaendert?"ok":"warn"}`}>
          ${r?`Eingecheckt: ${e.eingecheckt}${e.seit_einchecken_geaendert?" · seitdem geändert":""}`:"noch nicht eingecheckt"}</p>
        <div class="zeile">
          <input class="breit" placeholder="Kommentar (z. B. BK1–BK5 mit Anlage 2 verglichen)" .value=${ie}
            @input=${o=>{ie=o.target.value}}>
        </div>
        <div class="zeile"><button class="primaer" @click=${En}>✓ Stand einchecken</button>${d("einchecken")}</div>
        ${e.eincheckungen.length?a`
          <details class="protokoll"><summary>Protokoll (${e.eincheckungen.length})</summary>
            <ul>${[...e.eincheckungen].reverse().map(o=>a`
              <li><b>v${o.nr}</b> ${o.zeit} · ${o.stand.bohrungen[0]}/${o.stand.bohrungen[1]} Bohrungen, ${o.stand.schichten[0]}/${o.stand.schichten[1]} Schichten
                ${o.kommentar?a`<div class="leise klein">${o.kommentar}</div>`:u}</li>`)}</ul>
          </details>`:u}
      </section>

      <section class="abschnitt-flach">
        <h3>Export ${d("export")}</h3>
        <div class="export-liste">
          ${l.map(([o,h])=>a`<a class=${`knopf ${o==="ifc"?"primaer":""}`} href=${y.exportUrl(s.sig,o)}
            download>${h}</a>`)}
        </div>
      </section>

      ${t&&(t.hinweise.length||t.nicht_im_modell.length)?a`
        <section class="abschnitt-flach">
          <h3>Hinweise</h3>
          ${t.nicht_im_modell.length?a`<p class="klein"><b>Nicht im Modell:</b> ${t.nicht_im_modell.map(o=>`${o.code} (${o.grund})`).join(", ")}</p>`:u}
          ${t.hinweise.map(o=>a`<p class="klein">ℹ ${o}</p>`)}
        </section>`:u}
    </div>`}const _e={gutachten:"",bohrungen:"Weiter: Lage",lage:"Weiter: Einheiten",einheiten:"Weiter: Modell",modell:""};function Ln(e){const t=s.z;if(!t)return"";const n=t.pruefstand;return e==="gutachten"?"ok":e==="bohrungen"?n.unklassifiziert_offen?"warn":n.bohrungen[0]===n.bohrungen[1]&&n.bohrungen[1]?"ok":"":e==="lage"?t.viewer.bohrungen.filter(r=>r.x===null).length?"warn":"ok":e==="einheiten"||e==="modell"?s.modell?.fehler?"warn":s.modell?.bericht?"ok":"":""}function An(){const e=s.z;return a`
    <header class="kopf">
      <div class="marke" @click=${()=>N("gutachten")} title="Start">
        <span class="logo">⛰</span>
        <span><b>Geo_Agent</b> · Baugrundmodell</span>
      </div>
      <nav class="schritte" aria-label="Schritte">
        ${C.map(t=>{const n=t.id!=="gutachten"&&!e,i=Ln(t.id);return a`
            <button class=${`schritt-knopf ${s.schritt===t.id?"aktiv":""} ${i}`} ?disabled=${n}
              aria-current=${s.schritt===t.id?"step":"false"} @click=${()=>N(t.id)} title=${t.kurz}>
              <span class="nr">${i==="ok"&&s.schritt!==t.id?"✓":i==="warn"?"!":t.nr}</span>
              <span class="titel">${t.titel}</span>
            </button>`})}
      </nav>
      <div class="projekt">
        ${e?a`<span class="projektname" title=${e.dokumente.map(t=>t.datei).join(", ")}>${e.name}</span>
          <details class="menue">
            <summary title="Projekt">⋯</summary>
            <div class="menue-inhalt" @click=${Kn}>
              <button @click=${()=>N("gutachten")}>Anderes Projekt öffnen</button>
              <button @click=${Gn}>Alle Korrekturen verwerfen …</button>
              <a href="viewer.html" target="_blank" rel="noopener">Viewer allein öffnen</a>
            </div>
          </details>`:u}
      </div>
    </header>`}function Kn(e){e.currentTarget.closest("details")?.removeAttribute("open")}document.addEventListener("click",e=>{for(const t of document.querySelectorAll("details.menue[open]"))t.contains(e.target)||t.removeAttribute("open")});async function Gn(){if(!s.sig||!confirm("Alle Korrekturen, Lagen, Prüfhaken und Eincheckungen dieses Projekts verwerfen?"))return;await B(()=>y.zuruecksetzen(s.sig))&&await j(s.sig,"bohrungen")}function Fn(){if(s.schritt==="gutachten")return u;const e=C.findIndex(r=>r.id===s.schritt),t=C[e-1],n=C[e+1],i=s.z?.pruefstand;return a`
    <footer class="fuss">
      ${t?a`<button @click=${()=>N(t.id)}>← ${t.titel}</button>`:u}
      <span class="fuss-status">${i?`${i.bohrungen[0]}/${i.bohrungen[1]} Bohrungen · ${i.schichten[0]}/${i.schichten[1]} Schichten geprüft`:""}
        ${i?.unklassifiziert_offen?a` · <span class="warnung">⚠ ${i.unklassifiziert_offen} nicht klassifiziert</span>`:u}</span>
      <span class="fueller"></span>
      ${n&&_e[s.schritt]?a`<button class="primaer" @click=${()=>N(n.id)}>${_e[s.schritt]} →</button>`:u}
    </footer>`}function Hn(){return s.schritt==="gutachten"||!s.z?Xe():s.schritt==="bohrungen"?pn():s.schritt==="lage"?Mn():s.schritt==="einheiten"?Pn():Dn()}function Rn(){return a`
    ${An()}
    <main class=${`inhalt schritt-${s.schritt}`}>
      <section id="schritt" class="schritt">${Hn()}</section>
    </main>
    ${Fn()}
    <div class="meldungen" aria-live="polite">
      ${s.meldungen.map(e=>a`<div class=${`meldung ${e.art}`}>${e.text}</div>`)}
    </div>
    ${s.beschaeftigt?a`<div class="beschaeftigt"><div class="kreisel"></div><span>${s.beschaeftigt}</span></div>`:u}`}const Ne=document.getElementById("app");let K=null;function Tn(){Ie(Rn(),Ne);const e=Ne.querySelector("main");K||(K=document.createElement("div"),K.id="buehne",K.className="buehne"),K.parentElement!==e&&e.append(K),document.body.dataset.schritt=s.schritt}Ze(Tn);async function Te(){const[e,t,n]=location.hash.replace(/^#\/?/,"").split("/").map(decodeURIComponent);if(e&&e!==s.sig){if(await j(e,t||void 0),n&&s.schritt==="bohrungen"){const{bohrungWaehlen:i}=await je(async()=>{const{bohrungWaehlen:r}=await import("./store-Be2Pz4vb.js").then(l=>l.k);return{bohrungWaehlen:r}},__vite__mapDeps([0,1]),import.meta.url);await i(n)}}else e||await N("gutachten")}window.addEventListener("hashchange",()=>void Te());s.info=await B(()=>y.info())??null;p();await Pe();await Te();window.app=s;
