const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./store-KUki7-pU.js","./preload-helper-Ct5FWWRu.js"])))=>i.map(i=>d[i]);
import"./viewer-CQNpHX1F.js";import{_ as Re}from"./preload-helper-Ct5FWWRu.js";import{b as a,A as h,w as D,l as b,m as Te,k as fe,D as je}from"./lage-bkxEE1C3.js";import{S as s,n as f,o as j,v as B,a as y,m as T,p as _e,s as O,b as te,c as ue,d as g,z as ie,e as de,g as M,f as Oe,h as Ie,i as V}from"./store-KUki7-pU.js";import"./three.core-Dd2BBCN2.js";const le={ocr:["OCR für Scans","Liest gescannte PDFs und Text, der nur als Linien gezeichnet ist (SHX). Langsamer; bei Vektor-PDFs nicht nötig."],beispiele:["Beispiele","Fertig ausgewertete Gutachten zum Ausprobieren. Echte Daten: Berlin (georeferenziert) und Talheim (ohne Koordinaten)."],pruefstand:["Prüfstand","Wie viele Bohrungen und Schichten Sie geprüft haben. Eine Korrektur zählt als geprüft. Der Stand wird beim Einchecken festgehalten."],alle_pruefen:["Alle geprüft","Markiert alle Schichten aller Bohrungen im Modell als geprüft – nur wenn Sie alles mit dem Gutachten verglichen haben. Zurücknehmen ist jederzeit möglich."],warnung:["Warnung","Eine Schicht, deren Bodenart nicht erkannt wurde (unklassifiziert). Bodenart wählen, den Vorschlag nach Norm übernehmen oder die Schicht als geprüft markieren."],bodenart:["Bodenart","Klasse für das Modell; Farbe nach DIN 4023 (Kies gelb, Sand orange, Schluff oliv, Ton violett …). Gleiche Bodenarten werden zu Einheiten verbunden."],norm:["Deutung nach Norm","Die Beschreibung aus dem PDF gelesen nach DIN 4023 / DIN EN ISO 14688-1: Hauptanteil, Nebenanteile (schwach ' / stark ¯), Kurzzeichen, Bodengruppe nach DIN 18196 (nur wenn genannt), Konsistenz. Steht auch im IFC (CPset_Bodenansprache)."],vorschlag:["Vorschlag nach Norm","Für eine unklassifizierte Schicht schlägt die Normen-Datenbank eine Bodenart aus der Beschreibung vor. Sie wird nur übernommen, wenn Sie klicken; danach gilt die Schicht als korrigiert."],geprueft:["Geprüft","Haken: Schicht mit dem Gutachten verglichen. Steht im IFC (Geprueft) und im Prüfstand."],tiefe:["Tiefe","Ober- und Unterkante in m unter Geländeoberkante (GOK). Geändertes wird als korrigiert markiert."],gok:["GOK","Ansatzhöhe der Bohrung in m NHN. Aus dem PDF oder hier eingetragen (manuell). Ohne GOK bei allen Bohrungen rechnet das Modell relativ (Gelände = 0 m)."],koordinaten:["Koordinaten","Rechts- und Hochwert der Bohrung; leer lassen, wenn die Lage im Schritt Lage auf dem Plan gesetzt wird."],entfernen:["Entfernen","Die Bohrung kommt nicht ins Modell (sie bleibt in der Liste unter „Entfernt“ und lässt sich wiederherstellen)."],quelle:["Quelle im PDF","Die Seite des Gutachtens, auf der die Bohrung erkannt wurde; der Rahmen zeigt die gewählte Schicht."],lage_art:["Art der Lage","Koordinaten: Bohrungen mit Rechts-/Hochwert (aus dem PDF, eingetragen oder auf dem Lageplan gesetzt). Reihe: ohne Koordinaten nebeneinander mit Abständen bzw. Stationen aus dem Längsschnitt."],unterlage:["Unterlage","Lageplan (Draufsicht) oder Längsschnitt (Seitenansicht) als PDF. Er liegt im Viewer unter den Bohrungen; nach dem Kalibrieren werden die Bohrungen daraufgezogen."],massstab:["Maßstab","Zwei Punkte auf dem Plan anklicken, deren Abstand Sie kennen (Maßstabsleiste, Bemaßung, zwei Bohrungen), und die wahre Länge in m eintragen. Oder den Maßstab 1:n direkt angeben."],bezug:["Bezugspunkt","Ein Punkt im Plan mit bekannter Koordinate (Koordinatenkreuz, Bohrung mit Koordinaten): anklicken und Rechts-/Hochwert eintragen – im Längsschnitt Station und Höhe NHN."],drehung:["Drehung","Winkel, um den der Plan gegen Norden gedreht ist (gegen den Uhrzeigersinn positiv). Nordpfeil nach oben = 0°; Nordpfeil 10° nach links geneigt = 10°."],hoehe:["Höhenmaßstab","Längsschnitte sind oft überhöht (z. B. Länge 1:500, Höhe 1:100). Ohne Angabe gilt der Längenmaßstab."],epsg:["Koordinatensystem (EPSG)","System der Rechts-/Hochwerte aus der Liste wählen: in Deutschland meist ETRS89 / UTM 32N (25832), im Osten 33N (25833), ältere Pläne Gauß-Krüger (Rechtswert 7-stellig, erste Ziffer = Zone); dazu Schweiz und Österreich. Passen die Werte nicht zum System (Ziffernzahl, Zonenkennung), erscheint ein Hinweis. Steht im IFC (IfcMapConversion)."],sperren:["Sperren","Schloss zu: der Plan liegt fest und ändert sich nicht mehr; jetzt die Bohrungen ziehen. Auf dem Lageplan nur in x/y, im Längsschnitt entlang der Station – in der Höhe nur, wenn das PDF keine GOK hat."],deckkraft:["Deckkraft","Wie stark der Plan die Szene überdeckt."],ohne_lage:["Ohne Lage","Bohrungen ohne Koordinaten: mit der Maus aus der Liste auf den (gesperrten) Plan ziehen."],reihe:["Reihe","Bohrungen in einer Linie. Abstand zum Vorgänger je Bohrung eintragen (BK1 → BK2 10 m, BK2 → BK3 15 m) oder eine Station; ohne Eintrag gilt der Standardabstand. Reihenfolge mit den Pfeilen."],standardabstand:["Standardabstand","Abstand zwischen Bohrungen, für die nichts eingetragen ist (nur zur Anschauung, im Modell als schematisch markiert)."],durchmesser:["Durchmesser","Dicke der Bohrsäulen im Viewer und im IFC (Darstellung, nicht der Bohrdurchmesser im Feld). Automatisch wächst er mit der Modellgröße, damit Säulen auf langen Trassen sichtbar bleiben."],einheiten:["Einheiten","Modelleinheiten verbinden gleiche Bodenarten zwischen den Bohrungen (Sand 1, Kies, Sand 2). Umbenennen oder Bodenarten zusammenlegen (z. B. „Sand, Kies“ als eine Einheit); Reihenfolge von oben nach unten."],methode:["Interpolation","IDW: gewichtetes Mittel der Nachbarbohrungen, ruhig und sicher. Dünnplatten-Spline: glatte Flächen mit Trend, gut bei geneigten Schichten."],puffer:["Puffer","Wie weit das Modell über die Bohrungen hinausreicht. Automatisch: halber Bohrabstand (5–100 m)."],raster:["Raster","Maschenweite der Schichtflächen. Automatisch: Gebietsgröße/40, bei großen Modellen gröber (höchstens 30 000 Knoten)."],basis:["Modellbasis","Unterkante des Modells in m NHN. Automatisch: tiefste Endteufe."],gok_relativ:["Fehlende GOK","Hat keine Bohrung eine GOK, rechnet das Modell relativ (Gelände = 0 m) – markiert im IFC."],auto:["Automatisch nachführen","Jede Änderung (Tabelle, Lage, Einheiten) rechnet das Modell sofort neu."],einchecken:["Einchecken","Hält den Prüfstand fest (Zeit, Zähler, Fingerabdruck des Modells, Kommentar). Das exportierte IFC trägt ihn (CPset_Baugrundmodell.Pruefstand)."],export:["Export","IFC 4.3 mit Prüfstand, Bodenansprache je Schicht und Beschreibungen je Einheit; dazu Prüfbericht und die Daten als JSON."],ueberhoehung:["Überhöhung","Höhen im Viewer mal Faktor, damit dünne Schichten sichtbar werden. Die Koordinaten bleiben echt."]};let S=null,ce=null;function q(){S?.remove(),S=null,ce=null}function We(n,t){n.preventDefault(),n.stopPropagation();const e=n.currentTarget;if(ce===e){q();return}q();const[i,r]=le[t];S=document.createElement("div"),S.className="hilfe-blase",S.setAttribute("role","tooltip"),S.innerHTML="<strong></strong><p></p>",S.querySelector("strong").textContent=i,S.querySelector("p").textContent=r,document.body.append(S);const c=e.getBoundingClientRect(),o=S.getBoundingClientRect(),d=Math.min(Math.max(8,c.left+c.width/2-o.width/2),window.innerWidth-o.width-8),$=c.bottom+8+o.height>window.innerHeight?c.top-o.height-8:c.bottom+8;Object.assign(S.style,{left:`${d}px`,top:`${$}px`}),ce=e}document.addEventListener("click",n=>{S&&!S.contains(n.target)&&q()});document.addEventListener("keydown",n=>{n.key==="Escape"&&q()});const u=n=>a`<button type="button" class="hilfe" title=${le[n][0]} aria-label=${`Hilfe: ${le[n][0]}`}
    @click=${t=>We(t,n)}>?</button>`;let _=[],oe=!0,U=!1;async function Ne(n){for(;;){const t=await B(()=>y.auftrag(n));if(!t)return;if(s.auftrag=t,f(),t.fertig){s.auftrag=null;for(const e of t.fehler)T(e,"fehler",1e4);t.projekt?(_=[],await j(t.projekt,"bohrungen")):f();return}await new Promise(e=>setTimeout(e,600))}}async function Ze(){if(!_.length)return;const n=await B(()=>y.gutachten(_,oe&&!!s.info?.ocr));n&&await Ne(n.id)}async function Ue(n){const t=await B(()=>y.beispiel(n),"Beispiel wird geöffnet …");t?.projekt?await j(t.projekt,"bohrungen"):t?.auftrag&&await Ne(t.auftrag)}function be(n){_=[...n??[]].filter(t=>/\.(pdf|json)$/i.test(t.name)),n?.length&&!_.length&&T("Bitte PDF-Dateien wählen (oder eine Extraktion als JSON).","warn"),f()}async function Ce(n,t){confirm(`Projekt „${t}“ mit allen Korrekturen löschen? Das Gutachten selbst bleibt unberührt.`)&&(await B(()=>y.loeschen(n)),await _e())}function Ve(){const n=s.auftrag,t=!!s.info?.ocr;return a`
    <div class="seite-mitte">
      <section class="karte gross">
        <h2>Bodengutachten auswerten</h2>
        <p class="leise">Bohrprofile, Schichtenverzeichnisse oder ganze Gutachten als PDF – Vektor oder Scan. Die Bohrungen
          werden erkannt; im nächsten Schritt prüfen und korrigieren Sie sie.</p>
        ${n?a`
          <div class="fortschritt-karte" aria-live="polite">
            <div class="kreisel klein"></div>
            <div>
              <strong>${n.stand.datei||n.dateien[0]}</strong>
              <span class="leise">Datei ${n.stand.nr}/${n.stand.dateien||n.dateien.length}
                ${n.stand.seiten?a` · Seite ${n.stand.seite}/${n.stand.seiten}${n.stand.klasse?` · ${n.stand.klasse}`:""}`:" · wird geöffnet …"}</span>
              <progress max=${n.stand.seiten||1} value=${n.stand.seite}></progress>
            </div>
          </div>`:a`
          <label class=${`ablage ${U?"ueber":""}`}
            @dragover=${e=>{e.preventDefault(),U=!0,f()}}
            @dragleave=${()=>{U=!1,f()}}
            @drop=${e=>{e.preventDefault(),U=!1,be(e.dataTransfer?.files)}}>
            <input type="file" accept=".pdf,application/pdf,.json,application/json" multiple @change=${e=>be(e.target.files)}>
            <span class="ablage-icon">⇪</span>
            <strong>${_.length?_.map(e=>e.name).join(", "):"PDF hierher ziehen oder klicken"}</strong>
            <span class="leise">${_.length?`${_.length} Datei(en) bereit`:"mehrere Dateien möglich (z. B. Anlagen 2–4) · auch eine Extraktion als JSON"}</span>
          </label>
          <div class="zeile">
            <label class="schalter" title=${t?"":"nicht installiert: pip install -r requirements-ocr.txt"}>
              <input type="checkbox" .checked=${oe&&t} ?disabled=${!t} @change=${e=>{oe=e.target.checked}}>
              OCR für Scans ${t?"":"(nicht installiert)"}
            </label>${u("ocr")}
            <span class="fueller"></span>
            <button class="primaer" ?disabled=${!_.length} @click=${Ze}>Auswerten →</button>
          </div>`}
      </section>

      <div class="zwei-spalten">
        <section class="karte">
          <h3>Beispiele ${u("beispiele")}</h3>
          <ul class="auswahl-liste">
            ${(s.info?.beispiele??[]).map(e=>a`
              <li><button class="link" ?disabled=${!!n} @click=${()=>Ue(e.name)}>${e.titel}</button></li>`)}
          </ul>
        </section>
        <section class="karte">
          <h3>Zuletzt bearbeitet</h3>
          ${s.projekte.length?a`
            <table class="tabelle kompakt">
              <thead><tr><th>Projekt</th><th>Bohrungen</th><th>geprüft</th><th>geändert</th><th></th></tr></thead>
              <tbody>
                ${s.projekte.map(e=>a`
                  <tr>
                    <td><button class="link" @click=${()=>j(e.signatur)}>${e.name}</button>
                      <div class="leise klein">${e.dokumente.join(", ")}</div></td>
                    <td class="zahl">${e.bohrungen}</td>
                    <td class="zahl">${e.geprueft}${e.eincheckungen?a` · <span title="eingecheckt">✓${e.eincheckungen}</span>`:h}</td>
                    <td class="leise klein">${e.geaendert}</td>
                    <td><button class="symbol" title="Projekt löschen" aria-label="Projekt löschen" @click=${()=>Ce(e.signatur,e.name)}>🗑</button></td>
                  </tr>`)}
              </tbody>
            </table>`:a`<p class="leise">Noch keine Projekte. Ein Projekt entsteht beim ersten Auswerten und wird automatisch gesichert.</p>`}
        </section>
      </div>
    </div>`}const C="Deutschland · ETRS89 / UTM (amtlich)",A="Deutschland · Gauß-Krüger (alt)",J=[{code:25832,name:"ETRS89 / UTM Zone 32N",gruppe:C,e:[22e4,101e4],n:[503e4,614e4],hinweis:"Rechtswert 6-stellig, die meisten Länder"},{code:25833,name:"ETRS89 / UTM Zone 33N",gruppe:C,e:[15e4,7e5],n:[509e4,613e4],hinweis:"Rechtswert 6-stellig, Osten (Berlin, Brandenburg, Sachsen, MV)"},{code:4647,name:"ETRS89 / UTM 32N mit Zone (32…)",gruppe:C,e:[3223e4,33e6],n:[52e5,614e4],hinweis:"Rechtswert 8-stellig, beginnt mit 32"},{code:5650,name:"ETRS89 / UTM 33N mit Zone (33…)",gruppe:C,e:[3315e4,3354e4],n:[52e5,613e4],hinweis:"Rechtswert 8-stellig, beginnt mit 33"},{code:31466,name:"DHDN / Gauß-Krüger Zone 2",gruppe:A,e:[23e5,27e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 2"},{code:31467,name:"DHDN / Gauß-Krüger Zone 3",gruppe:A,e:[33e5,37e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 3"},{code:31468,name:"DHDN / Gauß-Krüger Zone 4",gruppe:A,e:[43e5,47e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 4"},{code:31469,name:"DHDN / Gauß-Krüger Zone 5",gruppe:A,e:[531e4,57e5],n:[52e5,613e4],hinweis:"Rechtswert 7-stellig, beginnt mit 5"},{code:2398,name:"Krassowski (42/83) / Gauß-Krüger Zone 4",gruppe:A,e:[43e5,47e5],n:[52e5,613e4],hinweis:"neue Länder vor ETRS89, Rechtswert beginnt mit 4"},{code:2399,name:"Krassowski (42/83) / Gauß-Krüger Zone 5",gruppe:A,e:[53e5,57e5],n:[52e5,613e4],hinweis:"neue Länder vor ETRS89, Rechtswert beginnt mit 5"},{code:3068,name:"DHDN / Soldner Berlin",gruppe:"Deutschland · andere",e:[-4e4,9e4],n:[-4e4,8e4],hinweis:"Berlin, alte Katasterkoordinaten (5-stellig)"},{code:2056,name:"CH1903+ / LV95",gruppe:"Schweiz",e:[245e4,287e4],n:[103e4,134e4],hinweis:"E 2 xxx xxx, N 1 xxx xxx"},{code:21781,name:"CH1903 / LV03",gruppe:"Schweiz",e:[45e4,87e4],n:[3e4,34e4],hinweis:"Y 6-stellig, X 5–6-stellig (alt)"},{code:31254,name:"MGI / Austria GK West",gruppe:"Österreich",e:[-11e4,17e4],n:[11e4,34e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31255,name:"MGI / Austria GK Central",gruppe:"Österreich",e:[-16e4,17e4],n:[9e4,46e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31256,name:"MGI / Austria GK East",gruppe:"Österreich",e:[-16e4,1e5],n:[1e5,48e4],hinweis:"Rechtswert um 0 (±), Hochwert ohne 5 000 000"},{code:31257,name:"MGI / Austria GK M28 (BMN)",gruppe:"Österreich",e:[4e4,32e4],n:[11e4,34e4],hinweis:"Bundesmeldenetz West"},{code:31258,name:"MGI / Austria GK M31 (BMN)",gruppe:"Österreich",e:[29e4,62e4],n:[9e4,46e4],hinweis:"Bundesmeldenetz Mitte"},{code:31259,name:"MGI / Austria GK M34 (BMN)",gruppe:"Österreich",e:[59e4,85e4],n:[1e5,48e4],hinweis:"Bundesmeldenetz Ost"},{code:32632,name:"WGS 84 / UTM Zone 32N",gruppe:"GPS (WGS 84)",e:[22e4,101e4],n:[503e4,614e4],hinweis:"wie ETRS89 / UTM 32N (Abweichung < 1 m)"},{code:32633,name:"WGS 84 / UTM Zone 33N",gruppe:"GPS (WGS 84)",e:[15e4,7e5],n:[509e4,613e4],hinweis:"wie ETRS89 / UTM 33N (Abweichung < 1 m)"}],qe=new Map(J.map(n=>[n.code,n]));function ge(n){return n?qe.get(n)??null:null}function Me(n){if(!n)return"ohne System (lokal)";const t=ge(n);return t?`EPSG ${n} · ${t.name}`:`EPSG ${n} (nicht in der Liste)`}const Ee=(n,t,e)=>t>=n.e[0]&&t<=n.e[1]&&e>=n.n[0]&&e<=n.n[1];function Je(n,t){return n===null||t===null||!Number.isFinite(n)||!Number.isFinite(t)?[]:J.filter(e=>e.gruppe!=="GPS (WGS 84)"&&Ee(e,n,t))}function De(n,t,e){if(t===null||e===null||!Number.isFinite(t)||!Number.isFinite(e))return null;const i=Je(t,e),r=i.slice(0,3).map(o=>`${o.code} (${o.name})`).join(", ");if(!n)return i.length?{ok:!1,text:`Kein System gewählt – die Werte passen zu ${r}.`}:null;const c=ge(n);return c?Ee(c,t,e)?{ok:!0,text:`passt zu EPSG ${n} (${c.hinweis})`}:{ok:!1,text:i.length?`Rechts-/Hochwert passen nicht zu EPSG ${n} (${c.hinweis}), aber zu ${r}.`:"Rechts-/Hochwert passen zu keinem System der Liste – Ziffern prüfen (z. B. fehlende Zonenkennung)."}:{ok:!1,text:`EPSG ${n} ist nicht in der Liste – bitte prüfen.`}}function Pe(n,t,e="Koordinatensystem"){const i=[...new Set(J.map(c=>c.gruppe))],r=n!==null&&!ge(n);return a`
    <select class="epsg" aria-label=${e} title=${Me(n)}
      @change=${c=>{const o=c.target.value;t(o===""?null:Number(o))}}>
      <option value="" .selected=${n===null}>– ohne (lokal) –</option>
      ${r?a`<option value=${String(n)} .selected=${!0}>EPSG ${n} – nicht in der Liste ⚠</option>`:h}
      ${i.map(c=>a`
        <optgroup label=${c}>
          ${J.filter(o=>o.gruppe===c).map(o=>a`
            <option value=${String(o.code)} .selected=${o.code===n}>${o.code} · ${o.name}</option>`)}
        </optgroup>`)}
    </select>`}const R=(n,t=2)=>n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});function Ae(n){for(const t of[.5,1,2,5,10,20,50,100])if(n/t<=12)return t;return 200}function Xe(n,t){const e=Math.max(1,...n.map(l=>l.bis)),i=12,r=(t.hoehe-i-14)/e,c=34,o=46,d=Ae(e),$=[];for(let l=0;l<=e+1e-9;l+=d)$.push(l);return a`<svg class="saeule" viewBox="0 0 150 ${t.hoehe}" width="150" height=${t.hoehe} role="img" aria-label="Bohrsäule">
    <defs>
      <pattern id="schraffur-warn" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="6" height="6" fill="#e6e6e6"></rect><line x1="0" y1="0" x2="0" y2="6" stroke="#f0a33a" stroke-width="3"></line>
      </pattern>
    </defs>
    ${$.map(l=>D`
      <line x1=${c-5} x2=${c} y1=${i+l*r} y2=${i+l*r} class="achse"></line>
      <text x=${c-7} y=${i+l*r+3} class="achse-text" text-anchor="end">${R(l,d<1?1:0)}</text>`)}
    <line x1=${c} x2=${c} y1=${i} y2=${i+e*r} class="achse"></line>
    ${n.map(l=>D`
      <g class=${`schicht ${l.k===t.gewaehlt?"gewaehlt":""} ${l.warn?"warn":""}`} @click=${()=>t.waehlen?.(l.k)}>
        <title>${l.titel}</title>
        <rect x=${c+4} y=${i+l.von*r} width=${o} height=${Math.max(1,(l.bis-l.von)*r)}
          fill=${l.warn?"url(#schraffur-warn)":l.farbe}></rect>
        ${l.geprueft?D`<text x=${c+o+9} y=${i+(l.von+l.bis)/2*r+4} class="haken">✓</text>`:h}
        ${(l.bis-l.von)*r>11?D`<text x=${c+o+22} y=${i+l.bis*r-2} class="tiefe">${R(l.bis)}</text>`:h}
      </g>`)}
  </svg>`}function Qe(n,t){const e=[...n.bohrungen].sort((p,W)=>p.x-W.x||p.y-W.y);if(!e.length)return h;const i=new Map(n.einheiten.map(p=>[p.name,p.farbe])),r=Math.max(...e.map(p=>p.gok)),c=Math.min(...e.map(p=>p.endteufe_nhn)),o=22,d=44,$=Math.max(38,Math.min(70,900/e.length)),l=d+e.length*$+10,w=(t.hoehe-o-10)/Math.max(1,r-c),v=p=>o+(r-p)*w,I=Ae(r-c),me=[];for(let p=Math.ceil(c/I)*I;p<=r+1e-9;p+=I)me.push(p);return a`<svg class="einheitenprofil" viewBox="0 0 ${l} ${t.hoehe}" width=${l} height=${t.hoehe} role="img"
      aria-label="Einheiten je Bohrung">
    ${me.map(p=>D`
      <line x1=${d-4} x2=${l} y1=${v(p)} y2=${v(p)} class="raster"></line>
      <text x=${d-6} y=${v(p)+3} class="achse-text" text-anchor="end">${R(p,I<1?1:0)}</text>`)}
    ${e.map((p,W)=>{const Z=d+W*$+$*.2,ae=$*.6;return D`
        <text x=${Z+ae/2} y=${o-8} class="code" text-anchor="middle">${p.code}</text>
        ${p.einheiten.filter(z=>z.status==="vorhanden"&&z.ok_modell-z.uk_modell>.001).map(z=>D`
          <rect x=${Z} y=${v(z.ok_modell)} width=${ae} height=${Math.max(.8,(z.ok_modell-z.uk_modell)*w)}
            fill=${i.get(z.einheit)??"#ccc"} class=${`einheit ${t.gewaehlt===z.einheit?"gewaehlt":""}`}
            @click=${()=>t.waehlen?.(z.einheit)}>
            <title>${p.code}: ${z.einheit} ${R(z.ok_modell)} bis ${R(z.uk_modell)} m NHN</title>
          </rect>`)}
        <line x1=${Z-3} x2=${Z+ae+3} y1=${v(p.endteufe_nhn)} y2=${v(p.endteufe_nhn)} class="endteufe"></line>`})}
  </svg>`}const X=(n,t=2)=>n==null?"":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),he=n=>{const t=n.target.value.trim().replace(",",".");return t===""?null:Number(t)},Ye=[["boden","Böden"],["organisch","Organisch"],["geologisch","Geologische Benennung"],["fels","Fels"],["anthropogen","Anthropogen"],["unbekannt","Nicht klassifiziert"]];let Q=null,se="",N=.5,$e=!1;function Y(n){const t=O(),e=t.findIndex(r=>r.id===s.bid),i=t[Math.min(t.length-1,Math.max(0,e+n))];i&&te(i.id)}function Ke(){const n=O(),t=ue(n.findIndex(e=>e.id===s.bid));t&&te(t)}async function Le(){const n=s.bid;if(!await g([{op:"bohrung_pruefen",id:n,wert:!0}],{leise:!0}))return;const t=ue(O().findIndex(e=>e.id===n));t&&t!==n&&await te(t)}async function ke(n){const t=s.z.pruefstand,e=n?`Alle Schichten aller ${t.bohrungen[1]} Bohrungen als geprüft markieren?`:"Die Prüfung aller Bohrungen zurücknehmen?";confirm(e)&&await g([{op:"alle_pruefen",wert:n}])}window.addEventListener("keydown",n=>{if(s.schritt!=="bohrungen"||n.ctrlKey||n.metaKey||n.altKey||n.target?.closest?.("input, select, textarea, [contenteditable]"))return;const e=n.key.toLowerCase();if(n.key==="ArrowDown"||e==="j")Y(1);else if(n.key==="ArrowUp"||e==="k")Y(-1);else if(e==="n")Ke();else if(e==="g")Le();else return;n.preventDefault()});async function en(n,t){const e=Number(n.id.split(":")[0]),i=(t[0]?.quelle.seite??n.seite)-1,r=`${s.sig}/${e}/${i}`;if(Q?.schluessel===r||se===r||!s.z?.dokumente[e]?.pdf)return;se=r;const c=await B(()=>y.seite(s.sig,e,i));se="",c&&(Q={schluessel:r,daten:c},f())}function nn(n){return n.entfernt?a`<span class="zeichen raus" title="nicht im Modell">–</span>`:n.offen>0?a`<span class="zeichen warn" title=${`${n.offen} Schicht(en) nicht klassifiziert`}>⚠</span>`:n.schichten_n&&n.schichten_geprueft===n.schichten_n?a`<span class="zeichen ok" title="alle Schichten geprüft">✓</span>`:a`<span class="zeichen" title="noch zu prüfen">○</span>`}function tn(){const n=s.z.bohrungen,t=O(),e=n.filter(i=>i.entfernt);return a`
    <aside class="bohrliste-app">
      <input class="suche" type="search" placeholder="Bohrung suchen …" .value=${s.filter}
        @input=${i=>{s.filter=i.target.value,f()}}>
      <ul class="bliste" role="listbox" aria-label="Bohrungen">
        ${t.map(i=>a`
          <li role="option" aria-selected=${String(i.id===s.bid)} class=${i.id===s.bid?"aktiv":""}
            @click=${()=>te(i.id)}>
            ${nn(i)}
            <span class="name">${i.code}</span>
            <span class="wert">${i.schichten_geprueft}/${i.schichten_n}</span>
            <button class="symbol leise-knopf" title="Aus dem Modell entfernen" aria-label=${`${i.code} entfernen`}
              @click=${r=>{r.stopPropagation(),g([{op:"entfernen",id:i.id}])}}>🗑</button>
          </li>`)}
      </ul>
      ${e.length?a`
        <details class="entfernt" ?open=${$e} @toggle=${i=>{$e=i.target.open}}>
          <summary>Entfernt / nicht im Modell (${e.length}) ${u("entfernen")}</summary>
          <ul class="bliste">
            ${e.map(i=>a`
              <li class="raus">
                <span class="name">${i.code}</span>
                <span class="wert klein">${i.doppelt_in?"doppelt":i.schichten_n?"":"ohne Schichten"}</span>
                <button class="link klein" ?disabled=${!i.schichten_n} @click=${()=>g([{op:"wiederherstellen",id:i.id}])}>wiederherstellen</button>
              </li>`)}
          </ul>
        </details>`:h}
      <p class="leise klein tasten">↑/↓ blättern · N nächste offene · G alle Schichten geprüft und weiter</p>
    </aside>`}function an(){const n=s.z.pruefstand,[t,e]=n.bohrungen,[i,r]=n.schichten;return a`
    <div class="pruefleiste">
      <div class="balken"><span>Bohrungen geprüft <b>${t}/${e}</b></span><progress max=${e||1} value=${t}></progress></div>
      <div class="balken"><span>Schichten geprüft <b>${i}/${r}</b></span><progress max=${r||1} value=${i}></progress></div>
      <span class=${`plakette ${n.unklassifiziert_offen?"warn":"ok"}`}>
        ${n.unklassifiziert_offen?`⚠ ${n.unklassifiziert_offen} Schicht(en) nicht klassifiziert`:"✓ keine offenen Warnungen"}</span>
      ${u("warnung")}
      <span class="fueller"></span>
      ${u("pruefstand")}
      <button @click=${()=>ke(!0)} ?disabled=${t===e&&i===r}>✓ Alle Bohrungen geprüft</button>
      <button class="leise-knopf" @click=${()=>ke(!1)} ?disabled=${!i}>Zurücknehmen</button>
      ${u("alle_pruefen")}
    </div>`}function E(n,t,e){return a`<label class="feld"><span>${n}${e?u(e):h}</span>${t}</label>`}function sn(n){const t=De(n.epsg,n.x,n.y);return t&&!t.ok?a`<p class="hinweise warn">⚠ ${t.text}</p>`:h}function rn(n){const t=O(),e=t.findIndex(r=>r.id===n.id),i=r=>c=>g([{op:"bohrung",id:n.id,feld:r,wert:he(c)}]);return a`
    <div class="detail-kopf">
      <div class="titelzeile">
        <h2>${n.code}</h2>
        <span class="leise">${n.dokument} · Seite ${n.seite}${n.doppelt_in?` · doppelt (auch in ${n.doppelt_in})`:""}</span>
        <span class="fueller"></span>
        <button title="Vorherige Bohrung (↑)" ?disabled=${e<=0} @click=${()=>Y(-1)}>↑ Vorherige</button>
        <button title="Nächste Bohrung (↓)" ?disabled=${e>=t.length-1} @click=${()=>Y(1)}>↓ Nächste</button>
        <button title="Nächste Bohrung mit offenen Schichten (N)" ?disabled=${!ue(e)} @click=${Ke}>⚠ Nächste offene</button>
      </div>
      <div class="felder">
        ${E("GOK [m NHN]",a`<input type="number" step="0.01" .value=${b(n.gok===null?"":String(n.gok))}
            placeholder="unbekannt" @change=${i("gok")}>
            <small class=${n.gok_quelle==="manuell"?"manuell":"leise"}>${n.gok_quelle||"fehlt"}</small>`,"gok")}
        ${E("Endteufe [m]",a`<output>${X(n.endteufe)}</output>`)}
        ${E("Rechtswert",a`<input type="number" step="0.01" .value=${b(n.x===null?"":String(n.x))} @change=${i("x")}>`,"koordinaten")}
        ${E("Hochwert",a`<input type="number" step="0.01" .value=${b(n.y===null?"":String(n.y))} @change=${i("y")}>`)}
        ${E("Koordinatensystem (EPSG)",Pe(n.epsg,r=>g([{op:"bohrung",id:n.id,feld:"epsg",wert:r}])),"epsg")}
        ${E("Ø Säule [m]",a`<input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${X(s.z.durchmesser??s.z.durchmesser_auto,1)}`}
            .value=${b(n.durchmesser===null?"":String(n.durchmesser))} @change=${i("durchmesser")}>`,"durchmesser")}
        ${E("Grundwasser",a`<output>${n.grundwasser||"–"}</output>`)}
      </div>
      ${sn(n)}
      ${n.hinweise.length?a`<p class="hinweise">ℹ ${n.hinweise.join(" · ")}</p>`:h}
    </div>`}function ln(n,t){const e=s.z.klassen,i=e.some(r=>r.klasse===t.bodenart);return a`
    <span class="farbfeld" style=${`background:${t.farbe}`}></span>
    <select aria-label="Bodenart" @change=${r=>g([{op:"schicht",id:n.id,k:t.k,feld:"bodenart",wert:r.target.value}])}>
      ${i?h:a`<option .selected=${!0} value=${t.bodenart}>${t.bodenart}</option>`}
      ${Ye.map(([r,c])=>a`
        <optgroup label=${c}>
          ${e.filter(o=>o.art===r).map(o=>a`
            <option value=${o.klasse} .selected=${o.klasse===t.bodenart}>${o.name}${o.din4023?` (${o.din4023})`:""}</option>`)}
        </optgroup>`)}
    </select>`}function cn(n,t){return a`
    <table class="tabelle schichten">
      <thead><tr>
        <th title="geprüft">✓ ${u("geprueft")}</th><th>von [m] ${u("tiefe")}</th><th>bis [m]</th>
        <th>Bodenart ${u("bodenart")}</th><th>Beschreibung (PDF)</th><th>nach Norm ${u("norm")}</th>
      </tr></thead>
      <tbody>
        ${t.map(e=>a`
          <tr class=${[e.offen?"warn":"",e.korrigiert?"korrigiert":"",e.k===s.k?"gewaehlt":""].join(" ")}
            @click=${()=>{s.k=e.k,f()}}>
            <td><input type="checkbox" .checked=${b(e.geprueft)} aria-label="geprüft"
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"geprueft",wert:i.target.checked}],{leise:!0})}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${b(String(e.von))}
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"oben",wert:he(i)}])}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${b(String(e.bis))}
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"unten",wert:he(i)}])}></td>
            <td class="bodenart">${ln(n,e)}
              ${e.offen?a`<div class="warnung">⚠ nicht klassifiziert</div>`:h}
              ${e.korrigiert?a`<div class="leise klein">korrigiert</div>`:h}</td>
            <td class="beschreibung">${e.beschreibung||a`<span class="leise">– keine Beschreibung –</span>`}
              ${e.hinweise.length?a`<div class="leise klein">${e.hinweise.join(" · ")}</div>`:h}</td>
            <td class="norm">
              ${e.norm.benennung?a`<div>${e.norm.benennung}</div>`:h}
              ${e.norm.din4023?a`<code title="Kurzzeichen nach DIN 4023">${e.norm.din4023}</code>`:h}
              ${e.norm.bodengruppe?a` <code title="Bodengruppe nach DIN 18196">${e.norm.bodengruppe}</code>`:h}
              ${[e.norm.konsistenz,e.norm.lagerung,e.norm.kalk,e.norm.bodenfarbe].filter(Boolean).length?a`<div class="leise klein">${[e.norm.konsistenz,e.norm.lagerung,e.norm.kalk,e.norm.bodenfarbe].filter(Boolean).join(" · ")}</div>`:h}
              ${e.norm.hinweise.length?a`<div class="klein hinweis-norm" title=${e.norm.hinweise.join(`
`)}>ℹ ${e.norm.hinweise[0]}${e.norm.hinweise.length>1?` (+${e.norm.hinweise.length-1})`:""}</div>`:h}
              ${e.vorschlag?a`
                <button class="vorschlag" @click=${i=>{i.stopPropagation(),g([{op:"vorschlag",id:n.id,k:e.k}])}}
                  title=${`Vorschlag nach Norm: ${e.vorschlag.benennung}${e.vorschlag.sicher?"":" (unsicher)"}`}>
                  → ${e.vorschlag.klasse} übernehmen</button>${u("vorschlag")}`:h}
            </td>
          </tr>`)}
      </tbody>
    </table>`}function on(n,t){en(n,t);const e=Number(n.id.split(":")[0]),i=!!s.z.dokumente[e]?.pdf,r=Q?.schluessel===`${s.sig}/${e}/${(t[0]?.quelle.seite??n.seite)-1}`?Q.daten:null,c=t.find(l=>l.k===s.k)??null,o=(l,w)=>{if(!l||!r)return h;const v=r.px_je_pt*N;return a`<div class=${`bbox ${w}`} style=${`left:${l[0]*v}px;top:${l[1]*v}px;width:${(l[2]-l[0])*v}px;height:${(l[3]-l[1])*v}px`}></div>`},d=t.map(l=>l.quelle.bbox).filter(l=>!!l&&l.length===4),$=d.length?[Math.min(...d.map(l=>l[0])),Math.min(...d.map(l=>l[1])),Math.max(...d.map(l=>l[2])),Math.max(...d.map(l=>l[3]))]:null;return a`
    <aside class="quelle-spalte">
      <div class="saeule-rahmen">
        ${Xe(t.map(l=>({k:l.k,von:l.von,bis:l.bis,farbe:l.farbe,warn:l.offen,geprueft:l.geprueft,titel:`${X(l.von)}–${X(l.bis)} m: ${l.bodenart}${l.beschreibung?` – ${l.beschreibung}`:""}`})),{hoehe:420,gewaehlt:s.k,waehlen:l=>{s.k=l,f()}})}
      </div>
      ${i?a`<div class="pdf-rahmen">
        <div class="pdf-kopf"><b>Quelle im PDF</b> ${u("quelle")}
          <span class="fueller"></span>
          ${i?a`<button class="symbol" title="kleiner" @click=${()=>{N=Math.max(.25,N/1.4),f()}}>−</button>
            <button class="symbol" title="größer" @click=${()=>{N=Math.min(1.5,N*1.4),f()}}>+</button>`:h}
        </div>
        ${r?a`
          ${hn($,r.px_je_pt*N)}
          <div class="pdf-seite">
            <div class="pdf-flaeche" style=${`width:${r.breite_pt*r.px_je_pt*N}px;height:${r.hoehe_pt*r.px_je_pt*N}px`}>
              <img src=${r.url} alt=${`Seite ${r.seite+1}`} draggable="false">
              ${o($,"saeule-bbox")}
              ${o(c?.quelle.bbox,"schicht-bbox")}
            </div>
          </div>`:a`<p class="leise klein">Seite wird geladen …</p>`}
      </div>`:h}
    </aside>`}let we="";function hn(n,t){const e=`${s.bid}/${N}`;return!n||we===e?h:(requestAnimationFrame(()=>{const i=document.querySelector(".pdf-seite");i&&(i.scrollLeft=Math.max(0,n[0]*t-i.clientWidth/3),i.scrollTop=Math.max(0,n[1]*t-40),we=e)}),h)}function un(){const n=s.z,t=s.details.get(s.bid),e=n.bohrungen.find(c=>c.id===s.bid),i=e?Number(e.id.split(":")[0]):0,r=!n.dokumente[i]?.pdf;return a`
    <div class=${`schritt-bohrungen ${r?"ohne-pdf":""}`}>
      ${an()}
      ${tn()}
      <section class="bohrung-detail">
        ${e?a`
          ${rn(e)}
          ${t?a`
            ${cn(e,t.schichten)}
            <div class="detail-fuss">
              <button class="primaer" title="Alle Schichten dieser Bohrung als geprüft markieren und zur nächsten offenen (G)"
                @click=${Le}>✓ Alle Schichten geprüft – weiter</button>
              <button class="leise-knopf" ?disabled=${!e.schichten_geprueft}
                @click=${()=>g([{op:"bohrung_pruefen",id:e.id,wert:!1}])}>Prüfung zurücknehmen</button>
              <span class="fueller"></span>
              <button class="gefahr" @click=${()=>g([{op:"entfernen",id:e.id}])}>🗑 Aus dem Modell entfernen</button>
            </div>`:a`<p class="leise">Schichten werden geladen …</p>`}`:a`<p class="leise">Links eine Bohrung wählen.</p>`}
      </section>
      ${e&&t?on(e,t.schichten):a`<aside class="quelle-spalte"></aside>`}
    </div>`}const Ge=(n,t=2)=>n==null||!Number.isFinite(n)?"":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),x=n=>{const t=n.target.value.trim().replace(",",".");return t===""?null:Number(t)};let m=null,ee="",H="plan";function ve(n){const t=n.unterlage;return t?`${t.sha}/${t.seite}/${t.art}/${JSON.stringify(t.kalibrierung)}`:""}function Fe(n){const t=n.unterlage;if(!t)return m=null;if(m&&m.schluessel===ve(n))return m;const e=t.kalibrierung,i=o=>o&&!("n"in o)?o:null,r=i(e?.massstab),c=i(e?.hoehe);return m={schluessel:ve(n),massArt:e?.massstab&&"n"in e.massstab?"n":"strecke",p1:r?{u:r.u1,v:r.v1}:null,p2:r?{u:r.u2,v:r.v2}:null,meter:r?.meter??null,n:e?.massstab&&"n"in e.massstab?e.massstab.n:null,hoeheArt:e?.hoehe?"n"in e.hoehe?"n":"strecke":"gleich",h1:c?{u:c.u1,v:c.v1}:null,h2:c?{u:c.u2,v:c.v2}:null,hoeheMeter:c?.meter??null,hoeheN:e?.hoehe&&"n"in e.hoehe?e.hoehe.n:null,bezug:e?.bezug?{u:e.bezug.u,v:e.bezug.v}:null,x:e?.bezug?.x??null,y:e?.bezug?.y??null,drehung:e?.drehung??0,epsg:e?.epsg??n.viewer.epsg??null},m}function pe(n,t=!1){const e=m,i=n.unterlage;if(!e||!i)return null;let r=null;if(e.massArt==="n"&&e.n&&e.n>0&&(r={n:e.n}),e.massArt==="strecke"&&e.p1&&e.p2&&e.meter&&e.meter>0&&(r={u1:e.p1.u,v1:e.p1.v,u2:e.p2.u,v2:e.p2.v,meter:e.meter}),!r||!e.bezug||e.x===null||e.y===null)return null;let c=null;return i.art==="schnitt"&&e.hoeheArt==="n"&&e.hoeheN&&e.hoeheN>0&&(c={n:e.hoeheN}),i.art==="schnitt"&&e.hoeheArt==="strecke"&&e.h1&&e.h2&&e.hoeheMeter&&e.hoeheMeter>0&&(c={u1:e.h1.u,v1:e.h1.v,u2:e.h2.u,v2:e.h2.v,meter:e.hoeheMeter}),{massstab:r,hoehe:c,bezug:{...e.bezug,x:e.x,y:e.y},drehung:i.art==="plan"?e.drehung:0,epsg:i.art==="plan"?e.epsg:null,gesperrt:t}}function k(){const n=s.z;s.entwurf=pe(n);const t=s.viewer;t&&m&&(t.editor.hilfsmarken({strecke:m.massArt==="strecke"?[m.p1,m.p2]:[],hoehe:m.hoeheArt==="strecke"?[m.h1,m.h2]:[],bezug:m.bezug}),s.entwurf&&t.editor.vorschau(s.entwurf)),f()}async function dn(n){const t=s.viewer;if(!t||!m)return;ee=n,f();const e=await t.editor.bildpunktWaehlen();if(ee="",!e||!m||s.z?.unterlage?.kalibrierung?.gesperrt){f();return}m[n]=e,k()}async function ze(n){s.viewer?.editor.waehlenAbbrechen();const t=pe(s.z,n);if(!t){T("Für die Kalibrierung fehlen Maßstab oder Bezugspunkt.","warn");return}await g([{op:"kalibrierung",wert:t}])&&(s.entwurf=null,T(n?"Plan kalibriert und gesperrt – jetzt die Bohrungen ziehen.":"Kalibrierung übernommen.","ok"),await s.viewer?.ansicht(s.z?.unterlage?.art==="schnitt"?"sued":"oben"))}async function gn(n){const t=s.z.unterlage;t?.kalibrierung&&await g([{op:"kalibrierung",wert:{...t.kalibrierung,gesperrt:n}}])}async function pn(n){const t=n.target,e=t.files?.[0];if(t.value="",!e)return;const i=await B(()=>y.unterlage(s.sig,e,H,0),"Unterlage wird gelesen …");i&&(ie(i),s.entwurf=null,f(),await de(),await s.viewer?.lageModus(!0),await s.viewer?.ansicht(i.unterlage?.art==="schnitt"?"sued":"oben"))}async function Se(n,t){const e=await B(()=>y.unterlageSeite(s.sig,n,t),"Seite wird gelesen …");e&&(ie(e),s.entwurf=null,f(),await de(),await s.viewer?.ansicht(t==="schnitt"?"sued":"oben"))}async function mn(){if(!confirm("Unterlage mit ihrer Kalibrierung entfernen? Gesetzte Bohrungen behalten ihre Lage."))return;const n=await B(()=>y.unterlageEntfernen(s.sig));n&&(ie(n),s.entwurf=null,f(),await de())}const G=(n,t,e=!0)=>a`<details class="abschnitt" ?open=${e}><summary>${n}</summary><div class="abschnitt-inhalt">${t}</div></details>`;function F(n,t,e,i){return a`<button class=${`punkt ${ee===t?"aktiv":""} ${e?"gesetzt":""}`} ?disabled=${i}
    @click=${()=>dn(t)}>${ee===t?"… im Plan klicken":e?`${n} ✓`:n}</button>`}function fn(n){const t=De(n.epsg,n.x,n.y);return t?a`<p class=${`klein ${t.ok?"ok":"warn"}`}>${t.ok?"✓":"⚠"} ${t.text}</p>`:h}function bn(n){const t=n.unterlage,e=Fe(n),i=!!t.kalibrierung?.gesperrt,r=t.art==="plan",c=e.p1&&e.p2?Math.hypot(e.p2.u-e.p1.u,e.p2.v-e.p1.v):null,o=pe(n),d=o?Te(o.massstab,t.mm_pro_px):null,$=n.viewer.bohrungen.filter(l=>l.x!==null&&(r?!/Plan|Viewer/.test(l.quelle):l.gok_bekannt));return a`
    <p class=${`status ${t.kalibrierung?i?"ok":"":"warn"}`}>
      ${t.kalibrierung?a`${i?"🔒 gesperrt · ":""}${fe(t)}${r?` · ${Me(t.kalibrierung.epsg)}`:""}`:"nicht kalibriert"}
      ${s.entwurf&&JSON.stringify({...s.entwurf,gesperrt:!1})!==JSON.stringify({...t.kalibrierung??{},gesperrt:!1})?a`<br><span class="leise">Vorschau: ${fe(t,s.entwurf)} (noch nicht übernommen)</span>`:h}
    </p>
    ${i?a`
      <p class="leise klein">Der Plan liegt fest. Bohrungen im Viewer ziehen – ${r?"nur in x/y":"entlang der Station; die Höhe nur ohne GOK aus dem PDF"}.</p>
      <button @click=${()=>gn(!1)}>🔓 Entsperren (neu kalibrieren)</button>`:a`
      <fieldset class="gruppe">
        <legend>1 · Maßstab ${u("massstab")}</legend>
        <div class="umschalter">
          <label><input type="radio" name="massart" .checked=${e.massArt==="strecke"} @change=${()=>{e.massArt="strecke",k()}}> Strecke messen</label>
          <label><input type="radio" name="massart" .checked=${e.massArt==="n"} @change=${()=>{e.massArt="n",k()}}> 1:n eingeben</label>
        </div>
        ${e.massArt==="strecke"?a`
          <div class="zeile">${F("Punkt 1","p1",e.p1,!1)}${F("Punkt 2","p2",e.p2,!1)}</div>
          <div class="zeile">
            <span class="leise klein">${c?`gemessen ${Ge(c,0)} px`:"zwei Punkte anklicken"}</span>
            <label class="inline">wahre Länge <input type="number" step="0.01" min="0" class="kurz" .value=${b(e.meter===null?"":String(e.meter))}
              @input=${l=>{e.meter=x(l),k()}}> m</label>
          </div>`:a`
          <label class="inline">Maßstab 1: <input type="number" step="1" min="1" class="kurz" .value=${b(e.n===null?"":String(e.n))}
            @input=${l=>{e.n=x(l),k()}}></label>`}
        ${d?a`<p class="leise klein">ergibt 1:${Math.round(d).toLocaleString("de-DE")}</p>`:h}
      </fieldset>
      ${r?h:a`
        <fieldset class="gruppe">
          <legend>Höhenmaßstab ${u("hoehe")}</legend>
          <div class="umschalter">
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="gleich"} @change=${()=>{e.hoeheArt="gleich",k()}}> wie Länge</label>
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="n"} @change=${()=>{e.hoeheArt="n",k()}}> 1:n</label>
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="strecke"} @change=${()=>{e.hoeheArt="strecke",k()}}> messen</label>
          </div>
          ${e.hoeheArt==="n"?a`<label class="inline">Höhe 1: <input type="number" step="1" min="1" class="kurz"
              .value=${b(e.hoeheN===null?"":String(e.hoeheN))} @input=${l=>{e.hoeheN=x(l),k()}}></label>`:h}
          ${e.hoeheArt==="strecke"?a`
            <div class="zeile">${F("Höhe oben","h1",e.h1,!1)}${F("Höhe unten","h2",e.h2,!1)}</div>
            <label class="inline">Höhenunterschied <input type="number" step="0.01" min="0" class="kurz"
              .value=${b(e.hoeheMeter===null?"":String(e.hoeheMeter))} @input=${l=>{e.hoeheMeter=x(l),k()}}> m</label>`:h}
        </fieldset>`}
      <fieldset class="gruppe">
        <legend>2 · Bezugspunkt ${u("bezug")}</legend>
        <div class="zeile">${F("Punkt im Plan wählen","bezug",e.bezug,!1)}</div>
        <div class="zeile">
          <label class="feld schmal"><span>${r?"Rechtswert":"Station [m]"}</span>
            <input type="number" step="0.01" .value=${b(e.x===null?"":String(e.x))} @input=${l=>{e.x=x(l),k()}}></label>
          <label class="feld schmal"><span>${r?"Hochwert":"Höhe [m NHN]"}</span>
            <input type="number" step="0.01" .value=${b(e.y===null?"":String(e.y))} @input=${l=>{e.y=x(l),k()}}></label>
        </div>
        ${r?a`
          <label class="feld breit"><span>Koordinatensystem (EPSG) ${u("epsg")}</span>
            ${Pe(e.epsg,l=>{e.epsg=l,k()})}</label>
          ${fn(e)}`:h}
        ${$.length?a`
          <label class="inline klein">oder von Bohrung
            <select @change=${l=>{const w=n.viewer.bohrungen.find(v=>v.id===l.target.value);w&&(e.x=w.x,e.y=r?w.y:w.gok,k())}}>
              <option value="">–</option>
              ${$.map(l=>a`<option value=${l.id}>${l.code}</option>`)}
            </select></label>`:h}
      </fieldset>
      ${r?a`
        <fieldset class="gruppe">
          <legend>3 · Drehung ${u("drehung")}</legend>
          <div class="zeile">
            <label class="inline"><input type="number" step="0.1" class="kurz" .value=${b(String(e.drehung))}
              @input=${l=>{e.drehung=x(l)??0,k()}}> ° gegen den Uhrzeigersinn</label>
          </div>
        </fieldset>`:h}
      <div class="zeile knopfzeile">
        <button ?disabled=${!o} @click=${()=>ze(!1)}>Übernehmen</button>
        <button class="primaer" ?disabled=${!o} @click=${()=>ze(!0)}>🔒 Übernehmen und sperren</button>
        ${u("sperren")}
      </div>
      ${t.kalibrierung?a`<button class="link klein" @click=${()=>g([{op:"kalibrierung",wert:null}])}>Kalibrierung zurücksetzen</button>`:h}`}`}function $n(n){const t=n.unterlage;return t?a`
    <p><b>${t.name}</b> <span class="leise">· ${t.art==="plan"?"Lageplan":"Längsschnitt"}</span></p>
    <div class="zeile">
      ${(t.seiten??1)>1?a`<label class="inline">Seite <select @change=${e=>Se(Number(e.target.value),t.art)}>
          ${Array.from({length:t.seiten},(e,i)=>a`<option value=${i} .selected=${i===t.seite}>${i+1}</option>`)}
        </select></label>`:h}
      <label class="inline">Ansicht <select @change=${e=>Se(t.seite,e.target.value)}>
        <option value="plan" .selected=${t.art==="plan"}>Lageplan</option>
        <option value="schnitt" .selected=${t.art==="schnitt"}>Längsschnitt</option>
      </select></label>
    </div>
    <label class="inline">Deckkraft ${u("deckkraft")}
      <input type="range" min="0.1" max="1" step="0.05" .value=${String(s.viewer?.editor.deckkraft??.85)}
        @input=${e=>{s.viewer&&(s.viewer.editor.deckkraft=Number(e.target.value),s.viewer.editor.bildSichtbarkeit())}}></label>
    <button class="link klein" @click=${mn}>Unterlage entfernen</button>`:a`
      <p class="leise klein">Lageplan (von oben) oder Längsschnitt (von der Seite) als PDF – er liegt im Viewer unter den Bohrungen.</p>
      <div class="umschalter">
        <label><input type="radio" name="neueart" .checked=${H==="plan"} @change=${()=>{H="plan"}}> Lageplan</label>
        <label><input type="radio" name="neueart" .checked=${H==="schnitt"} @change=${()=>{H="schnitt"}}> Längsschnitt</label>
      </div>
      <label class="datei-knopf"><input type="file" accept=".pdf,application/pdf" @change=${pn}>PDF wählen …</label>`}function kn(n){const t=n.unterlage,e=!t||!!t.kalibrierung?.gesperrt,i=n.viewer.bohrungen.filter(c=>c.x===null),r=n.lage_modus==="reihe";return a`
    ${e?h:a`<p class="warnung">Erst kalibrieren und sperren (🔒) – dann die Bohrungen ziehen.</p>`}
    ${i.length?a`
      <p class="klein">Ohne Lage (${i.length}) – in den Viewer ziehen ${u("ohne_lage")}</p>
      <div class="parkplatz">
        ${i.map(c=>a`<span class="park ${e?"":"gesperrt"}" title="In den Viewer ziehen"
          @pointerdown=${o=>s.viewer?.editor.ziehenStart(o,c.id,!0)}>${c.code}</span>`)}
      </div>`:a`<p class="leise klein">Alle Bohrungen im Modell haben eine Lage.</p>`}
    ${r?wn(n):h}`}function wn(n){const t=n.reihe.map(i=>i.id),e=(i,r)=>{const c=[...t],[o]=c.splice(i,1);c.splice(Math.max(0,Math.min(c.length,i+r)),0,o),g([{op:"reihe",reihenfolge:c}],{leise:!0})};return a`
    <div class="zeile">
      <label class="inline">Standardabstand ${u("standardabstand")}
        <input type="number" step="1" min="1" class="kurz" .value=${b(String(n.reihe_standard))}
          @change=${i=>g([{op:"reihe",standard:x(i)}])}> m</label>
    </div>
    <table class="tabelle kompakt reihe">
      <thead><tr><th></th><th>Bohrung</th><th>Abstand [m] ${u("reihe")}</th><th>Station [m]</th></tr></thead>
      <tbody>
        ${n.reihe.map((i,r)=>a`
          <tr>
            <td class="pfeile"><button class="symbol" ?disabled=${r===0} title="nach vorn" @click=${()=>e(r,-1)}>▲</button><button class="symbol"
              ?disabled=${r===t.length-1} title="nach hinten" @click=${()=>e(r,1)}>▼</button></td>
            <td>${i.code}</td>
            <td><input type="number" step="0.1" min="0" class="kurz" ?disabled=${r===0} .value=${b(i.abstand===null?"":String(i.abstand))}
              @change=${c=>g([{op:"reihe",abstand:{[i.id]:x(c)}}],{leise:!0})}></td>
            <td><input type="number" step="0.1" class="kurz" .value=${b(String(i.station))} title=${i.quelle_text}
              @change=${c=>g([{op:"reihe",station:{[i.id]:x(c)}}],{leise:!0})}></td>
          </tr>`)}
      </tbody>
    </table>`}function vn(n){const t=s.viewer;t&&(!n.unterlage||n.unterlage.kalibrierung?.gesperrt||!m?t.editor.hilfsmarken({}):t.editor.hilfsmarken({strecke:m.massArt==="strecke"?[m.p1,m.p2]:[],hoehe:m.hoeheArt==="strecke"?[m.h1,m.h2]:[],bezug:m.bezug}))}function zn(){const n=s.z;return Fe(n),vn(n),a`
    <div class="app-panel links">
      ${G(a`Lage der Bohrungen ${u("lage_art")}`,a`
        <div class="umschalter">
          <label><input type="radio" name="lagemodus" .checked=${n.lage_modus==="koordinaten"}
            @change=${()=>g([{op:"lage_modus",wert:"koordinaten"}])}> Koordinaten (Lageplan)</label>
          <label><input type="radio" name="lagemodus" .checked=${n.lage_modus==="reihe"}
            @change=${()=>g([{op:"lage_modus",wert:"reihe"}])}> Reihe (Längsschnitt)</label>
        </div>`)}
      ${G(a`Unterlage ${u("unterlage")}`,$n(n))}
      ${n.unterlage?G(a`Kalibrieren`,bn(n)):h}
      ${G(a`Bohrungen setzen`,kn(n))}
      ${G(a`Darstellung`,a`
        <label class="inline">Ø Bohrsäulen ${u("durchmesser")}
          <input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${Ge(n.durchmesser_auto,1)}`}
            .value=${b(n.durchmesser===null?"":String(n.durchmesser))}
            @change=${t=>g([{op:"durchmesser",wert:x(t)}])}> m</label>
        <p class="leise klein">Je Bohrung im Schritt Bohrungen (Ø Säule). Leer = automatisch nach Modellgröße.</p>`,!1)}
      ${n.hinweise.length?a`<div class="hinweisliste">${n.hinweise.map(t=>a`<p class="klein">ℹ ${t}</p>`)}</div>`:h}
    </div>`}const P=(n,t=1)=>n==null?"–":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});let K="",re=null,ye="";function Sn(){const n=s.z.einstellungen,t=(r,c)=>g([{op:"einstellungen",[r]:c}]),e=(r,c,o,d,$)=>{const l=n[r];return a`
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${l===null} @change=${w=>t(r,w.target.checked?null:d)}> ${c} automatisch</label>${u($)}
        ${l===null?h:a`<input type="number" step="any" class="kurz" .value=${b(String(l))}
          @change=${w=>t(r,Number(w.target.value))}> ${o}`}
      </div>`},i=s.modell?.bericht?.parameter??{};return a`
    <section class="karte">
      <h3>Modell</h3>
      <div class="einstellung">
        <span>Interpolation ${u("methode")}</span>
        <label class="inline"><input type="radio" name="methode" .checked=${n.methode==="idw"} @change=${()=>t("methode","idw")}> IDW</label>
        <label class="inline"><input type="radio" name="methode" .checked=${n.methode==="tps"} @change=${()=>t("methode","tps")}> Dünnplatten-Spline</label>
      </div>
      ${e("puffer","Puffer","m",Number(i.puffer_m??20),"puffer")}
      ${e("raster","Raster","m",Number(i.raster_m??5),"raster")}
      ${e("basis","Modellbasis","m NHN",Math.floor(Number(i.basis_nhn??0)),"basis")}
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${n.gok_relativ} @change=${r=>t("gok_relativ",r.target.checked)}> fehlende GOK: Gelände = 0 m</label>${u("gok_relativ")}
      </div>
      ${i.raster_m!==void 0?a`<p class="leise klein">gerechnet: Puffer ${P(Number(i.puffer_m),0)} m · Raster ${P(Number(i.raster_m))} m ·
        Basis ${P(Number(i.basis_nhn),2)} m NHN · Fläche ${P(Number(i.flaeche_m2)/1e4,2)} ha</p>`:h}
    </section>`}function yn(){const n=s.modell?.bericht;if(!n)return h;const t=s.z.vorgabe??n.vorlage_einheiten,e=JSON.stringify(t);(!re||ye!==e)&&(re=t.map(c=>({name:c.name,bodenarten:c.bodenarten.join(", ")})),ye=e);const i=re,r=()=>g([{op:"vorgabe",wert:i.filter(c=>c.name.trim()).map(c=>({name:c.name.trim(),bodenarten:c.bodenarten.split(",").map(o=>o.trim()).filter(Boolean)}))}]);return a`
    <section class="karte">
      <h3>Einheiten festlegen ${u("einheiten")}</h3>
      <p class="leise klein">${s.z.vorgabe?"Vorgegeben (eigene Einheiten).":"Automatisch korreliert – hier umbenennen oder Bodenarten zusammenlegen."}</p>
      <table class="tabelle kompakt vorgabe">
        <colgroup><col class="pfeil"><col><col><col class="weg"></colgroup>
        <thead><tr><th></th><th>Einheit</th><th>Bodenarten (mit Komma)</th><th></th></tr></thead>
        <tbody>
          ${i.map((c,o)=>a`
            <tr>
              <td class="pfeile"><button class="symbol" ?disabled=${o===0} @click=${()=>{i.splice(o-1,0,...i.splice(o,1)),f()}}>▲</button><button
                class="symbol" ?disabled=${o===i.length-1} @click=${()=>{i.splice(o+1,0,...i.splice(o,1)),f()}}>▼</button></td>
              <td><input .value=${b(c.name)} @input=${d=>{c.name=d.target.value}}></td>
              <td><input .value=${b(c.bodenarten)} @input=${d=>{c.bodenarten=d.target.value}}></td>
              <td><button class="symbol" title="Zeile löschen" @click=${()=>{i.splice(o,1),f()}}>✕</button></td>
            </tr>`)}
        </tbody>
      </table>
      <div class="zeile knopfzeile">
        <button class="link" @click=${()=>{i.push({name:"",bodenarten:""}),f()}}>+ Zeile</button>
        <span class="fueller"></span>
        <button ?disabled=${!s.z.vorgabe} @click=${()=>g([{op:"vorgabe",wert:null}])}>Automatisch korrelieren</button>
        <button class="primaer" @click=${r}>Mit diesen Einheiten rechnen</button>
      </div>
    </section>`}function xn(){const n=s.modell,t=n?.bericht,e=t?.einheiten.find(i=>i.name===K);return a`
    <div class="schritt-einheiten">
      <div class="spalte">
        ${Sn()}
        ${yn()}
      </div>
      <div class="spalte breit">
        ${s.rechnet?a`<div class="karte"><div class="kreisel klein"></div> Modell wird gerechnet …</div>`:h}
        ${n?.fehler?a`<div class="karte warnung">Noch kein Modell: ${n.fehler}
          <button class="link" @click=${()=>M("lage")}>→ Lage setzen</button></div>`:h}
        ${t?a`
          <section class="karte">
            <h3>Einheiten (${t.einheiten.length})</h3>
            <table class="tabelle einheiten">
              <thead><tr><th></th><th>Einheit</th><th>Bodenarten</th><th>Volumen [m³]</th><th>max. Mächtigkeit [m]</th>
                <th title="in Bohrungen vorhanden / fehlt / unter der Endteufe">✓ / – / ?</th><th>Hinweise</th></tr></thead>
              <tbody>
                ${t.einheiten.map(i=>a`
                  <tr class=${i.name===K?"gewaehlt":""} @click=${()=>{K=K===i.name?"":i.name,f()}}>
                    <td><span class="farbfeld" style=${`background:${i.farbe}`}></span></td>
                    <td><b>${i.name}</b></td>
                    <td>${i.bodenarten.join(", ")}</td>
                    <td class="zahl">${Math.round(i.volumen_m3).toLocaleString("de-DE")}</td>
                    <td class="zahl">${P(i.maechtigkeit_max_m,2)}</td>
                    <td class="zahl">${i.bohrungen.vorhanden.length} / ${i.bohrungen.fehlt.length} / ${i.bohrungen.unbekannt.length}</td>
                    <td class="klein">${i.hinweise.join("; ")}</td>
                  </tr>`)}
              </tbody>
            </table>
          </section>
          <section class="karte profil-karte">
            <h3>Einheiten je Bohrung <span class="leise klein">(m NHN, Klick wählt die Einheit)</span></h3>
            <div class="profil-scroll">${Qe(t,{hoehe:380,gewaehlt:K,waehlen:i=>{K=i,f()}})}</div>
          </section>
          ${e?a`
            <section class="karte">
              <h3><span class="farbfeld" style=${`background:${e.farbe}`}></span> ${e.name}: Beschreibungen aus dem PDF</h3>
              <table class="tabelle kompakt">
                <thead><tr><th>Bohrung</th><th>Tiefe [m]</th><th>Bodenart</th><th>Beschreibung</th></tr></thead>
                <tbody>${e.schichten.map(i=>a`
                  <tr><td>${i.bohrung}</td><td class="zahl">${P(i.von,2)}–${P(i.bis,2)}</td><td>${i.bodenart??"unklassifiziert"}</td>
                    <td>${i.beschreibung||a`<span class="leise">–</span>`}</td></tr>`)}</tbody>
              </table>
            </section>`:h}`:h}
      </div>
    </div>`}let ne="";async function Bn(){const n=await B(()=>y.einchecken(s.sig,ne));n&&(ie(n.zustand),ne="",T(`Eingecheckt: v${n.eintrag.nr} · ${n.eintrag.stand.bohrungen[0]}/${n.eintrag.stand.bohrungen[1]} Bohrungen geprüft`,"ok"),f())}function _n(){const n=s.z,t=s.modell,e=t?.bericht,i=n.pruefstand,r=n.eincheckungen[n.eincheckungen.length-1],c=[["ifc","Baugrundmodell (IFC 4.3)"],["bericht","Prüfbericht (JSON)"],["einheiten","Einheiten-Vorlage (JSON)"],["extraktion","Extraktion (JSON)"],["eingabe","Modell-Eingabe mit Korrekturen (JSON)"],["projekt","Projektstand (JSON)"]];return a`
    <div class="app-panel rechts">
      <section class="abschnitt-flach">
        <h3>Modell</h3>
        ${s.rechnet?a`<p><span class="kreisel klein"></span> wird gerechnet …</p>`:h}
        ${t?.fehler?a`<p class="warnung">Noch kein Modell: ${t.fehler}</p>
          <button class="link" @click=${()=>M("lage")}>→ Lage setzen</button>`:h}
        ${e?a`
          <ul class="kennzahlen">
            <li><b>${e.einheiten.length}</b> Einheiten</li>
            <li><b>${e.bohrungen.length}</b> Bohrungen im Modell</li>
            <li class=${e.epsg?"":"warn"}>${e.epsg?`EPSG:${e.epsg}`:"lokales System"}</li>
            <li class=${e.pruefungen.alle_koerper_geschlossen?"ok":"warn"}>${e.pruefungen.alle_koerper_geschlossen?"Körper geschlossen":"Körper offen"}</li>
            <li class=${e.pruefungen.max_abweichung_an_bohrungen_m<.01?"ok":"warn"}>Abweichung an Bohrungen ${e.pruefungen.max_abweichung_an_bohrungen_m.toFixed(3)} m</li>
          </ul>`:h}
        <div class="zeile">
          <label class="inline"><input type="checkbox" .checked=${n.auto} @change=${o=>g([{op:"auto",wert:o.target.checked}],{leise:!0})}>
            automatisch nachführen</label>${u("auto")}
          <span class="fueller"></span>
          <button ?disabled=${s.rechnet} @click=${()=>Oe()}>Neu rechnen</button>
        </div>
        <label class="inline">Überhöhung ${u("ueberhoehung")}
          <select @change=${async o=>{const d=Number(o.target.value);await s.viewer?.ueberhoehen(d),await g([{op:"ueberhoehung",wert:d}],{leise:!0})}}>
            ${[1,2,5,10,20].map(o=>a`<option value=${o} .selected=${n.ueberhoehung===o}>${o}×</option>`)}
          </select></label>
      </section>

      <section class="abschnitt-flach">
        <h3>Prüfstand ${u("pruefstand")}</h3>
        <div class="balken"><span>Bohrungen <b>${i.bohrungen[0]}/${i.bohrungen[1]}</b></span><progress max=${i.bohrungen[1]||1} value=${i.bohrungen[0]}></progress></div>
        <div class="balken"><span>Schichten <b>${i.schichten[0]}/${i.schichten[1]}</b></span><progress max=${i.schichten[1]||1} value=${i.schichten[0]}></progress></div>
        <p class="klein">${i.unklassifiziert_offen?a`<span class="warnung">⚠ ${i.unklassifiziert_offen} Schicht(en) nicht klassifiziert</span>
          <button class="link" @click=${()=>M("bohrungen")}>prüfen</button>`:a`<span class="ok">✓ keine offenen Warnungen</span>`}
          · ${i.korrigiert} korrigiert · ${i.manuelle_lage} Lagen manuell · ${i.entfernt} entfernt</p>
        <p class=${`klein ${r&&!n.seit_einchecken_geaendert?"ok":"warn"}`}>
          ${r?`Eingecheckt: ${n.eingecheckt}${n.seit_einchecken_geaendert?" · seitdem geändert":""}`:"noch nicht eingecheckt"}</p>
        <div class="zeile">
          <input class="breit" placeholder="Kommentar (z. B. BK1–BK5 mit Anlage 2 verglichen)" .value=${ne}
            @input=${o=>{ne=o.target.value}}>
        </div>
        <div class="zeile"><button class="primaer" @click=${Bn}>✓ Stand einchecken</button>${u("einchecken")}</div>
        ${n.eincheckungen.length?a`
          <details class="protokoll"><summary>Protokoll (${n.eincheckungen.length})</summary>
            <ul>${[...n.eincheckungen].reverse().map(o=>a`
              <li><b>v${o.nr}</b> ${o.zeit} · ${o.stand.bohrungen[0]}/${o.stand.bohrungen[1]} Bohrungen, ${o.stand.schichten[0]}/${o.stand.schichten[1]} Schichten
                ${o.kommentar?a`<div class="leise klein">${o.kommentar}</div>`:h}</li>`)}</ul>
          </details>`:h}
      </section>

      <section class="abschnitt-flach">
        <h3>Export ${u("export")}</h3>
        <div class="export-liste">
          ${c.map(([o,d])=>a`<a class=${`knopf ${o==="ifc"?"primaer":""}`} href=${y.exportUrl(s.sig,o)}
            download>${d}</a>`)}
        </div>
      </section>

      ${t&&(t.hinweise.length||t.nicht_im_modell.length)?a`
        <section class="abschnitt-flach">
          <h3>Hinweise</h3>
          ${t.nicht_im_modell.length?a`<p class="klein"><b>Nicht im Modell:</b> ${t.nicht_im_modell.map(o=>`${o.code} (${o.grund})`).join(", ")}</p>`:h}
          ${t.hinweise.map(o=>a`<p class="klein">ℹ ${o}</p>`)}
        </section>`:h}
    </div>`}const xe={gutachten:"",bohrungen:"Weiter: Lage",lage:"Weiter: Einheiten",einheiten:"Weiter: Modell",modell:""};function Nn(n){const t=s.z;if(!t)return"";const e=t.pruefstand;return n==="gutachten"?"ok":n==="bohrungen"?e.unklassifiziert_offen?"warn":e.bohrungen[0]===e.bohrungen[1]&&e.bohrungen[1]?"ok":"":n==="lage"?t.viewer.bohrungen.filter(r=>r.x===null).length?"warn":"ok":n==="einheiten"||n==="modell"?s.modell?.fehler?"warn":s.modell?.bericht?"ok":"":""}function Mn(){const n=s.z;return a`
    <header class="kopf">
      <div class="marke" @click=${()=>M("gutachten")} title="Start">
        <span class="logo">⛰</span>
        <span><b>Geo_Agent</b> · Baugrundmodell</span>
      </div>
      <nav class="schritte" aria-label="Schritte">
        ${V.map(t=>{const e=t.id!=="gutachten"&&!n,i=Nn(t.id);return a`
            <button class=${`schritt-knopf ${s.schritt===t.id?"aktiv":""} ${i}`} ?disabled=${e}
              aria-current=${s.schritt===t.id?"step":"false"} @click=${()=>M(t.id)} title=${t.kurz}>
              <span class="nr">${i==="ok"&&s.schritt!==t.id?"✓":i==="warn"?"!":t.nr}</span>
              <span class="titel">${t.titel}</span>
            </button>`})}
      </nav>
      <div class="projekt">
        ${n?a`<span class="projektname" title=${n.dokumente.map(t=>t.datei).join(", ")}>${n.name}</span>
          <details class="menue">
            <summary title="Projekt">⋯</summary>
            <div class="menue-inhalt" @click=${En}>
              <button @click=${()=>M("gutachten")}>Anderes Projekt öffnen</button>
              <button @click=${Dn}>Alle Korrekturen verwerfen …</button>
              <a href="viewer.html" target="_blank" rel="noopener">Viewer allein öffnen</a>
            </div>
          </details>`:h}
      </div>
    </header>`}function En(n){n.currentTarget.closest("details")?.removeAttribute("open")}document.addEventListener("click",n=>{for(const t of document.querySelectorAll("details.menue[open]"))t.contains(n.target)||t.removeAttribute("open")});async function Dn(){if(!s.sig||!confirm("Alle Korrekturen, Lagen, Prüfhaken und Eincheckungen dieses Projekts verwerfen?"))return;await B(()=>y.zuruecksetzen(s.sig))&&await j(s.sig,"bohrungen")}function Pn(){if(s.schritt==="gutachten")return h;const n=V.findIndex(r=>r.id===s.schritt),t=V[n-1],e=V[n+1],i=s.z?.pruefstand;return a`
    <footer class="fuss">
      ${t?a`<button @click=${()=>M(t.id)}>← ${t.titel}</button>`:h}
      <span class="fuss-status">${i?`${i.bohrungen[0]}/${i.bohrungen[1]} Bohrungen · ${i.schichten[0]}/${i.schichten[1]} Schichten geprüft`:""}
        ${i?.unklassifiziert_offen?a` · <span class="warnung">⚠ ${i.unklassifiziert_offen} nicht klassifiziert</span>`:h}</span>
      <span class="fueller"></span>
      ${e&&xe[s.schritt]?a`<button class="primaer" @click=${()=>M(e.id)}>${xe[s.schritt]} →</button>`:h}
    </footer>`}function An(){return s.schritt==="gutachten"||!s.z?Ve():s.schritt==="bohrungen"?un():s.schritt==="lage"?zn():s.schritt==="einheiten"?xn():_n()}function Kn(){return a`
    ${Mn()}
    <main class=${`inhalt schritt-${s.schritt}`}>
      <section id="schritt" class="schritt">${An()}</section>
    </main>
    ${Pn()}
    <div class="meldungen" aria-live="polite">
      ${s.meldungen.map(n=>a`<div class=${`meldung ${n.art}`}>${n.text}</div>`)}
    </div>
    ${s.beschaeftigt?a`<div class="beschaeftigt"><div class="kreisel"></div><span>${s.beschaeftigt}</span></div>`:h}`}const Be=document.getElementById("app");let L=null;function Ln(){je(Kn(),Be);const n=Be.querySelector("main");L||(L=document.createElement("div"),L.id="buehne",L.className="buehne"),L.parentElement!==n&&n.append(L),document.body.dataset.schritt=s.schritt}Ie(Ln);async function He(){const[n,t,e]=location.hash.replace(/^#\/?/,"").split("/").map(decodeURIComponent);if(n&&n!==s.sig){if(await j(n,t||void 0),e&&s.schritt==="bohrungen"){const{bohrungWaehlen:i}=await Re(async()=>{const{bohrungWaehlen:r}=await import("./store-KUki7-pU.js").then(c=>c.j);return{bohrungWaehlen:r}},__vite__mapDeps([0,1]),import.meta.url);await i(e)}}else n||await M("gutachten")}window.addEventListener("hashchange",()=>void He());s.info=await B(()=>y.info())??null;f();await _e();await He();window.app=s;
