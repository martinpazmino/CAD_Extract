const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./store-BI5Rw7m0.js","./preload-helper-Ct5FWWRu.js"])))=>i.map(i=>d[i]);
import"./viewer-CQNpHX1F.js";import{_ as Ae}from"./preload-helper-Ct5FWWRu.js";import{b as a,A as h,w as A,l as f,m as De,k as de,D as Ee}from"./lage-Crfzt0CM.js";import{S as s,n as b,o as G,v as B,a as x,m as O,p as ye,s as I,b as Y,c as ce,d as g,z as ee,e as oe,g as M,f as Le,h as Ke,i as q}from"./store-BI5Rw7m0.js";import"./three.core-Dd2BBCN2.js";const ae={ocr:["OCR für Scans","Liest gescannte PDFs und Text, der nur als Linien gezeichnet ist (SHX). Langsamer; bei Vektor-PDFs nicht nötig."],beispiele:["Beispiele","Fertig ausgewertete Gutachten zum Ausprobieren. Echte Daten: Berlin (georeferenziert) und Talheim (ohne Koordinaten)."],pruefstand:["Prüfstand","Wie viele Bohrungen und Schichten Sie geprüft haben. Eine Korrektur zählt als geprüft. Der Stand wird beim Einchecken festgehalten."],alle_pruefen:["Alle geprüft","Markiert alle Schichten aller Bohrungen im Modell als geprüft – nur wenn Sie alles mit dem Gutachten verglichen haben. Zurücknehmen ist jederzeit möglich."],warnung:["Warnung","Eine Schicht, deren Bodenart nicht erkannt wurde (unklassifiziert). Bodenart wählen, den Vorschlag nach Norm übernehmen oder die Schicht als geprüft markieren."],bodenart:["Bodenart","Klasse für das Modell; Farbe nach DIN 4023 (Kies gelb, Sand orange, Schluff oliv, Ton violett …). Gleiche Bodenarten werden zu Einheiten verbunden."],norm:["Deutung nach Norm","Die Beschreibung aus dem PDF gelesen nach DIN 4023 / DIN EN ISO 14688-1: Hauptanteil, Nebenanteile (schwach ' / stark ¯), Kurzzeichen, Bodengruppe nach DIN 18196 (nur wenn genannt), Konsistenz. Steht auch im IFC (CPset_Bodenansprache)."],vorschlag:["Vorschlag nach Norm","Für eine unklassifizierte Schicht schlägt die Normen-Datenbank eine Bodenart aus der Beschreibung vor. Sie wird nur übernommen, wenn Sie klicken; danach gilt die Schicht als korrigiert."],geprueft:["Geprüft","Haken: Schicht mit dem Gutachten verglichen. Steht im IFC (Geprueft) und im Prüfstand."],tiefe:["Tiefe","Ober- und Unterkante in m unter Geländeoberkante (GOK). Geändertes wird als korrigiert markiert."],gok:["GOK","Ansatzhöhe der Bohrung in m NHN. Aus dem PDF oder hier eingetragen (manuell). Ohne GOK bei allen Bohrungen rechnet das Modell relativ (Gelände = 0 m)."],koordinaten:["Koordinaten","Rechts- und Hochwert der Bohrung; leer lassen, wenn die Lage im Schritt Lage auf dem Plan gesetzt wird."],entfernen:["Entfernen","Die Bohrung kommt nicht ins Modell (sie bleibt in der Liste unter „Entfernt“ und lässt sich wiederherstellen)."],quelle:["Quelle im PDF","Die Seite des Gutachtens, auf der die Bohrung erkannt wurde; der Rahmen zeigt die gewählte Schicht."],lage_art:["Art der Lage","Koordinaten: Bohrungen mit Rechts-/Hochwert (aus dem PDF, eingetragen oder auf dem Lageplan gesetzt). Reihe: ohne Koordinaten nebeneinander mit Abständen bzw. Stationen aus dem Längsschnitt."],unterlage:["Unterlage","Lageplan (Draufsicht) oder Längsschnitt (Seitenansicht) als PDF. Er liegt im Viewer unter den Bohrungen; nach dem Kalibrieren werden die Bohrungen daraufgezogen."],massstab:["Maßstab","Zwei Punkte auf dem Plan anklicken, deren Abstand Sie kennen (Maßstabsleiste, Bemaßung, zwei Bohrungen), und die wahre Länge in m eintragen. Oder den Maßstab 1:n direkt angeben."],bezug:["Bezugspunkt","Ein Punkt im Plan mit bekannter Koordinate (Koordinatenkreuz, Bohrung mit Koordinaten): anklicken und Rechts-/Hochwert eintragen – im Längsschnitt Station und Höhe NHN."],drehung:["Drehung","Winkel, um den der Plan gegen Norden gedreht ist (gegen den Uhrzeigersinn positiv). Nordpfeil nach oben = 0°; Nordpfeil 10° nach links geneigt = 10°."],hoehe:["Höhenmaßstab","Längsschnitte sind oft überhöht (z. B. Länge 1:500, Höhe 1:100). Ohne Angabe gilt der Längenmaßstab."],epsg:["EPSG","Koordinatensystem der Plankoordinaten, z. B. 25832 (ETRS89 / UTM 32N) oder 25833. Steht dann im IFC (IfcMapConversion)."],sperren:["Sperren","Schloss zu: der Plan liegt fest und ändert sich nicht mehr; jetzt die Bohrungen ziehen. Auf dem Lageplan nur in x/y, im Längsschnitt entlang der Station – in der Höhe nur, wenn das PDF keine GOK hat."],deckkraft:["Deckkraft","Wie stark der Plan die Szene überdeckt."],ohne_lage:["Ohne Lage","Bohrungen ohne Koordinaten: mit der Maus aus der Liste auf den (gesperrten) Plan ziehen."],reihe:["Reihe","Bohrungen in einer Linie. Abstand zum Vorgänger je Bohrung eintragen (BK1 → BK2 10 m, BK2 → BK3 15 m) oder eine Station; ohne Eintrag gilt der Standardabstand. Reihenfolge mit den Pfeilen."],standardabstand:["Standardabstand","Abstand zwischen Bohrungen, für die nichts eingetragen ist (nur zur Anschauung, im Modell als schematisch markiert)."],durchmesser:["Durchmesser","Dicke der Bohrsäulen im Viewer und im IFC (Darstellung, nicht der Bohrdurchmesser im Feld). Automatisch wächst er mit der Modellgröße, damit Säulen auf langen Trassen sichtbar bleiben."],einheiten:["Einheiten","Modelleinheiten verbinden gleiche Bodenarten zwischen den Bohrungen (Sand 1, Kies, Sand 2). Umbenennen oder Bodenarten zusammenlegen (z. B. „Sand, Kies“ als eine Einheit); Reihenfolge von oben nach unten."],methode:["Interpolation","IDW: gewichtetes Mittel der Nachbarbohrungen, ruhig und sicher. Dünnplatten-Spline: glatte Flächen mit Trend, gut bei geneigten Schichten."],puffer:["Puffer","Wie weit das Modell über die Bohrungen hinausreicht. Automatisch: halber Bohrabstand (5–100 m)."],raster:["Raster","Maschenweite der Schichtflächen. Automatisch: Gebietsgröße/40, bei großen Modellen gröber (höchstens 30 000 Knoten)."],basis:["Modellbasis","Unterkante des Modells in m NHN. Automatisch: tiefste Endteufe."],gok_relativ:["Fehlende GOK","Hat keine Bohrung eine GOK, rechnet das Modell relativ (Gelände = 0 m) – markiert im IFC."],auto:["Automatisch nachführen","Jede Änderung (Tabelle, Lage, Einheiten) rechnet das Modell sofort neu."],einchecken:["Einchecken","Hält den Prüfstand fest (Zeit, Zähler, Fingerabdruck des Modells, Kommentar). Das exportierte IFC trägt ihn (CPset_Baugrundmodell.Pruefstand)."],export:["Export","IFC 4.3 mit Prüfstand, Bodenansprache je Schicht und Beschreibungen je Einheit; dazu Prüfbericht und die Daten als JSON."],ueberhoehung:["Überhöhung","Höhen im Viewer mal Faktor, damit dünne Schichten sichtbar werden. Die Koordinaten bleiben echt."]};let y=null,se=null;function C(){y?.remove(),y=null,se=null}function je(n,t){n.preventDefault(),n.stopPropagation();const e=n.currentTarget;if(se===e){C();return}C();const[i,l]=ae[t];y=document.createElement("div"),y.className="hilfe-blase",y.setAttribute("role","tooltip"),y.innerHTML="<strong></strong><p></p>",y.querySelector("strong").textContent=i,y.querySelector("p").textContent=l,document.body.append(y);const c=e.getBoundingClientRect(),o=y.getBoundingClientRect(),d=Math.min(Math.max(8,c.left+c.width/2-o.width/2),window.innerWidth-o.width-8),$=c.bottom+8+o.height>window.innerHeight?c.top-o.height-8:c.bottom+8;Object.assign(y.style,{left:`${d}px`,top:`${$}px`}),se=e}document.addEventListener("click",n=>{y&&!y.contains(n.target)&&C()});document.addEventListener("keydown",n=>{n.key==="Escape"&&C()});const u=n=>a`<button type="button" class="hilfe" title=${ae[n][0]} aria-label=${`Hilfe: ${ae[n][0]}`}
    @click=${t=>je(t,n)}>?</button>`;let _=[],le=!0,W=!1;async function Se(n){for(;;){const t=await B(()=>x.auftrag(n));if(!t)return;if(s.auftrag=t,b(),t.fertig){s.auftrag=null;for(const e of t.fehler)O(e,"fehler",1e4);t.projekt?(_=[],await G(t.projekt,"bohrungen")):b();return}await new Promise(e=>setTimeout(e,600))}}async function Fe(){if(!_.length)return;const n=await B(()=>x.gutachten(_,le&&!!s.info?.ocr));n&&await Se(n.id)}async function He(n){const t=await B(()=>x.beispiel(n),"Beispiel wird geöffnet …");t?.projekt?await G(t.projekt,"bohrungen"):t?.auftrag&&await Se(t.auftrag)}function ge(n){_=[...n??[]].filter(t=>/\.(pdf|json)$/i.test(t.name)),n?.length&&!_.length&&O("Bitte PDF-Dateien wählen (oder eine Extraktion als JSON).","warn"),b()}async function Oe(n,t){confirm(`Projekt „${t}“ mit allen Korrekturen löschen? Das Gutachten selbst bleibt unberührt.`)&&(await B(()=>x.loeschen(n)),await ye())}function Ge(){const n=s.auftrag,t=!!s.info?.ocr;return a`
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
          <label class=${`ablage ${W?"ueber":""}`}
            @dragover=${e=>{e.preventDefault(),W=!0,b()}}
            @dragleave=${()=>{W=!1,b()}}
            @drop=${e=>{e.preventDefault(),W=!1,ge(e.dataTransfer?.files)}}>
            <input type="file" accept=".pdf,application/pdf,.json,application/json" multiple @change=${e=>ge(e.target.files)}>
            <span class="ablage-icon">⇪</span>
            <strong>${_.length?_.map(e=>e.name).join(", "):"PDF hierher ziehen oder klicken"}</strong>
            <span class="leise">${_.length?`${_.length} Datei(en) bereit`:"mehrere Dateien möglich (z. B. Anlagen 2–4) · auch eine Extraktion als JSON"}</span>
          </label>
          <div class="zeile">
            <label class="schalter" title=${t?"":"nicht installiert: pip install -r requirements-ocr.txt"}>
              <input type="checkbox" .checked=${le&&t} ?disabled=${!t} @change=${e=>{le=e.target.checked}}>
              OCR für Scans ${t?"":"(nicht installiert)"}
            </label>${u("ocr")}
            <span class="fueller"></span>
            <button class="primaer" ?disabled=${!_.length} @click=${Fe}>Auswerten →</button>
          </div>`}
      </section>

      <div class="zwei-spalten">
        <section class="karte">
          <h3>Beispiele ${u("beispiele")}</h3>
          <ul class="auswahl-liste">
            ${(s.info?.beispiele??[]).map(e=>a`
              <li><button class="link" ?disabled=${!!n} @click=${()=>He(e.name)}>${e.titel}</button></li>`)}
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
                    <td><button class="link" @click=${()=>G(e.signatur)}>${e.name}</button>
                      <div class="leise klein">${e.dokumente.join(", ")}</div></td>
                    <td class="zahl">${e.bohrungen}</td>
                    <td class="zahl">${e.geprueft}${e.eincheckungen?a` · <span title="eingecheckt">✓${e.eincheckungen}</span>`:h}</td>
                    <td class="leise klein">${e.geaendert}</td>
                    <td><button class="symbol" title="Projekt löschen" aria-label="Projekt löschen" @click=${()=>Oe(e.signatur,e.name)}>🗑</button></td>
                  </tr>`)}
              </tbody>
            </table>`:a`<p class="leise">Noch keine Projekte. Ein Projekt entsteht beim ersten Auswerten und wird automatisch gesichert.</p>`}
        </section>
      </div>
    </div>`}const H=(n,t=2)=>n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});function xe(n){for(const t of[.5,1,2,5,10,20,50,100])if(n/t<=12)return t;return 200}function Ie(n,t){const e=Math.max(1,...n.map(r=>r.bis)),i=12,l=(t.hoehe-i-14)/e,c=34,o=46,d=xe(e),$=[];for(let r=0;r<=e+1e-9;r+=d)$.push(r);return a`<svg class="saeule" viewBox="0 0 150 ${t.hoehe}" width="150" height=${t.hoehe} role="img" aria-label="Bohrsäule">
    <defs>
      <pattern id="schraffur-warn" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="6" height="6" fill="#e6e6e6"></rect><line x1="0" y1="0" x2="0" y2="6" stroke="#f0a33a" stroke-width="3"></line>
      </pattern>
    </defs>
    ${$.map(r=>A`
      <line x1=${c-5} x2=${c} y1=${i+r*l} y2=${i+r*l} class="achse"></line>
      <text x=${c-7} y=${i+r*l+3} class="achse-text" text-anchor="end">${H(r,d<1?1:0)}</text>`)}
    <line x1=${c} x2=${c} y1=${i} y2=${i+e*l} class="achse"></line>
    ${n.map(r=>A`
      <g class=${`schicht ${r.k===t.gewaehlt?"gewaehlt":""} ${r.warn?"warn":""}`} @click=${()=>t.waehlen?.(r.k)}>
        <title>${r.titel}</title>
        <rect x=${c+4} y=${i+r.von*l} width=${o} height=${Math.max(1,(r.bis-r.von)*l)}
          fill=${r.warn?"url(#schraffur-warn)":r.farbe}></rect>
        ${r.geprueft?A`<text x=${c+o+9} y=${i+(r.von+r.bis)/2*l+4} class="haken">✓</text>`:h}
        ${(r.bis-r.von)*l>11?A`<text x=${c+o+22} y=${i+r.bis*l-2} class="tiefe">${H(r.bis)}</text>`:h}
      </g>`)}
  </svg>`}function Te(n,t){const e=[...n.bohrungen].sort((p,R)=>p.x-R.x||p.y-R.y);if(!e.length)return h;const i=new Map(n.einheiten.map(p=>[p.name,p.farbe])),l=Math.max(...e.map(p=>p.gok)),c=Math.min(...e.map(p=>p.endteufe_nhn)),o=22,d=44,$=Math.max(38,Math.min(70,900/e.length)),r=d+e.length*$+10,v=(t.hoehe-o-10)/Math.max(1,l-c),w=p=>o+(l-p)*v,T=xe(l-c),ue=[];for(let p=Math.ceil(c/T)*T;p<=l+1e-9;p+=T)ue.push(p);return a`<svg class="einheitenprofil" viewBox="0 0 ${r} ${t.hoehe}" width=${r} height=${t.hoehe} role="img"
      aria-label="Einheiten je Bohrung">
    ${ue.map(p=>A`
      <line x1=${d-4} x2=${r} y1=${w(p)} y2=${w(p)} class="raster"></line>
      <text x=${d-6} y=${w(p)+3} class="achse-text" text-anchor="end">${H(p,T<1?1:0)}</text>`)}
    ${e.map((p,R)=>{const V=d+R*$+$*.2,ne=$*.6;return A`
        <text x=${V+ne/2} y=${o-8} class="code" text-anchor="middle">${p.code}</text>
        ${p.einheiten.filter(z=>z.status==="vorhanden"&&z.ok_modell-z.uk_modell>.001).map(z=>A`
          <rect x=${V} y=${w(z.ok_modell)} width=${ne} height=${Math.max(.8,(z.ok_modell-z.uk_modell)*v)}
            fill=${i.get(z.einheit)??"#ccc"} class=${`einheit ${t.gewaehlt===z.einheit?"gewaehlt":""}`}
            @click=${()=>t.waehlen?.(z.einheit)}>
            <title>${p.code}: ${z.einheit} ${H(z.ok_modell)} bis ${H(z.uk_modell)} m NHN</title>
          </rect>`)}
        <line x1=${V-3} x2=${V+ne+3} y1=${w(p.endteufe_nhn)} y2=${w(p.endteufe_nhn)} class="endteufe"></line>`})}
  </svg>`}const U=(n,t=2)=>n==null?"":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),re=n=>{const t=n.target.value.trim().replace(",",".");return t===""?null:Number(t)},Re=[["boden","Böden"],["organisch","Organisch"],["geologisch","Geologische Benennung"],["fels","Fels"],["anthropogen","Anthropogen"],["unbekannt","Nicht klassifiziert"]];let J=null,te="",N=.5,pe=!1;function Z(n){const t=I(),e=t.findIndex(l=>l.id===s.bid),i=t[Math.min(t.length-1,Math.max(0,e+n))];i&&Y(i.id)}function Be(){const n=I(),t=ce(n.findIndex(e=>e.id===s.bid));t&&Y(t)}async function _e(){const n=s.bid;if(!await g([{op:"bohrung_pruefen",id:n,wert:!0}],{leise:!0}))return;const t=ce(I().findIndex(e=>e.id===n));t&&t!==n&&await Y(t)}async function me(n){const t=s.z.pruefstand,e=n?`Alle Schichten aller ${t.bohrungen[1]} Bohrungen als geprüft markieren?`:"Die Prüfung aller Bohrungen zurücknehmen?";confirm(e)&&await g([{op:"alle_pruefen",wert:n}])}window.addEventListener("keydown",n=>{if(s.schritt!=="bohrungen"||n.ctrlKey||n.metaKey||n.altKey||n.target?.closest?.("input, select, textarea, [contenteditable]"))return;const e=n.key.toLowerCase();if(n.key==="ArrowDown"||e==="j")Z(1);else if(n.key==="ArrowUp"||e==="k")Z(-1);else if(e==="n")Be();else if(e==="g")_e();else return;n.preventDefault()});async function Ve(n,t){const e=Number(n.id.split(":")[0]),i=(t[0]?.quelle.seite??n.seite)-1,l=`${s.sig}/${e}/${i}`;if(J?.schluessel===l||te===l||!s.z?.dokumente[e]?.pdf)return;te=l;const c=await B(()=>x.seite(s.sig,e,i));te="",c&&(J={schluessel:l,daten:c},b())}function We(n){return n.entfernt?a`<span class="zeichen raus" title="nicht im Modell">–</span>`:n.offen>0?a`<span class="zeichen warn" title=${`${n.offen} Schicht(en) nicht klassifiziert`}>⚠</span>`:n.schichten_n&&n.schichten_geprueft===n.schichten_n?a`<span class="zeichen ok" title="alle Schichten geprüft">✓</span>`:a`<span class="zeichen" title="noch zu prüfen">○</span>`}function qe(){const n=s.z.bohrungen,t=I(),e=n.filter(i=>i.entfernt);return a`
    <aside class="bohrliste-app">
      <input class="suche" type="search" placeholder="Bohrung suchen …" .value=${s.filter}
        @input=${i=>{s.filter=i.target.value,b()}}>
      <ul class="bliste" role="listbox" aria-label="Bohrungen">
        ${t.map(i=>a`
          <li role="option" aria-selected=${String(i.id===s.bid)} class=${i.id===s.bid?"aktiv":""}
            @click=${()=>Y(i.id)}>
            ${We(i)}
            <span class="name">${i.code}</span>
            <span class="wert">${i.schichten_geprueft}/${i.schichten_n}</span>
            <button class="symbol leise-knopf" title="Aus dem Modell entfernen" aria-label=${`${i.code} entfernen`}
              @click=${l=>{l.stopPropagation(),g([{op:"entfernen",id:i.id}])}}>🗑</button>
          </li>`)}
      </ul>
      ${e.length?a`
        <details class="entfernt" ?open=${pe} @toggle=${i=>{pe=i.target.open}}>
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
    </aside>`}function Ce(){const n=s.z.pruefstand,[t,e]=n.bohrungen,[i,l]=n.schichten;return a`
    <div class="pruefleiste">
      <div class="balken"><span>Bohrungen geprüft <b>${t}/${e}</b></span><progress max=${e||1} value=${t}></progress></div>
      <div class="balken"><span>Schichten geprüft <b>${i}/${l}</b></span><progress max=${l||1} value=${i}></progress></div>
      <span class=${`plakette ${n.unklassifiziert_offen?"warn":"ok"}`}>
        ${n.unklassifiziert_offen?`⚠ ${n.unklassifiziert_offen} Schicht(en) nicht klassifiziert`:"✓ keine offenen Warnungen"}</span>
      ${u("warnung")}
      <span class="fueller"></span>
      ${u("pruefstand")}
      <button @click=${()=>me(!0)} ?disabled=${t===e&&i===l}>✓ Alle Bohrungen geprüft</button>
      <button class="leise-knopf" @click=${()=>me(!1)} ?disabled=${!i}>Zurücknehmen</button>
      ${u("alle_pruefen")}
    </div>`}function P(n,t,e){return a`<label class="feld"><span>${n}${e?u(e):h}</span>${t}</label>`}function Ue(n){const t=I(),e=t.findIndex(l=>l.id===n.id),i=l=>c=>g([{op:"bohrung",id:n.id,feld:l,wert:re(c)}]);return a`
    <div class="detail-kopf">
      <div class="titelzeile">
        <h2>${n.code}</h2>
        <span class="leise">${n.dokument} · Seite ${n.seite}${n.doppelt_in?` · doppelt (auch in ${n.doppelt_in})`:""}</span>
        <span class="fueller"></span>
        <button title="Vorherige Bohrung (↑)" ?disabled=${e<=0} @click=${()=>Z(-1)}>↑ Vorherige</button>
        <button title="Nächste Bohrung (↓)" ?disabled=${e>=t.length-1} @click=${()=>Z(1)}>↓ Nächste</button>
        <button title="Nächste Bohrung mit offenen Schichten (N)" ?disabled=${!ce(e)} @click=${Be}>⚠ Nächste offene</button>
      </div>
      <div class="felder">
        ${P("GOK [m NHN]",a`<input type="number" step="0.01" .value=${f(n.gok===null?"":String(n.gok))}
            placeholder="unbekannt" @change=${i("gok")}>
            <small class=${n.gok_quelle==="manuell"?"manuell":"leise"}>${n.gok_quelle||"fehlt"}</small>`,"gok")}
        ${P("Endteufe [m]",a`<output>${U(n.endteufe)}</output>`)}
        ${P("Rechtswert",a`<input type="number" step="0.01" .value=${f(n.x===null?"":String(n.x))} @change=${i("x")}>`,"koordinaten")}
        ${P("Hochwert",a`<input type="number" step="0.01" .value=${f(n.y===null?"":String(n.y))} @change=${i("y")}>`)}
        ${P("EPSG",a`<input type="number" step="1" class="kurz" .value=${f(n.epsg===null?"":String(n.epsg))} @change=${i("epsg")}>`,"epsg")}
        ${P("Ø Säule [m]",a`<input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${U(s.z.durchmesser??s.z.durchmesser_auto,1)}`}
            .value=${f(n.durchmesser===null?"":String(n.durchmesser))} @change=${i("durchmesser")}>`,"durchmesser")}
        ${P("Grundwasser",a`<output>${n.grundwasser||"–"}</output>`)}
      </div>
      ${n.hinweise.length?a`<p class="hinweise">ℹ ${n.hinweise.join(" · ")}</p>`:h}
    </div>`}function Je(n,t){const e=s.z.klassen,i=e.some(l=>l.klasse===t.bodenart);return a`
    <span class="farbfeld" style=${`background:${t.farbe}`}></span>
    <select aria-label="Bodenart" @change=${l=>g([{op:"schicht",id:n.id,k:t.k,feld:"bodenart",wert:l.target.value}])}>
      ${i?h:a`<option .selected=${!0} value=${t.bodenart}>${t.bodenart}</option>`}
      ${Re.map(([l,c])=>a`
        <optgroup label=${c}>
          ${e.filter(o=>o.art===l).map(o=>a`
            <option value=${o.klasse} .selected=${o.klasse===t.bodenart}>${o.name}${o.din4023?` (${o.din4023})`:""}</option>`)}
        </optgroup>`)}
    </select>`}function Ze(n,t){return a`
    <table class="tabelle schichten">
      <thead><tr>
        <th title="geprüft">✓ ${u("geprueft")}</th><th>von [m] ${u("tiefe")}</th><th>bis [m]</th>
        <th>Bodenart ${u("bodenart")}</th><th>Beschreibung (PDF)</th><th>nach Norm ${u("norm")}</th>
      </tr></thead>
      <tbody>
        ${t.map(e=>a`
          <tr class=${[e.offen?"warn":"",e.korrigiert?"korrigiert":"",e.k===s.k?"gewaehlt":""].join(" ")}
            @click=${()=>{s.k=e.k,b()}}>
            <td><input type="checkbox" .checked=${f(e.geprueft)} aria-label="geprüft"
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"geprueft",wert:i.target.checked}],{leise:!0})}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${f(String(e.von))}
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"oben",wert:re(i)}])}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${f(String(e.bis))}
              @change=${i=>g([{op:"schicht",id:n.id,k:e.k,feld:"unten",wert:re(i)}])}></td>
            <td class="bodenart">${Je(n,e)}
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
    </table>`}function Qe(n,t){Ve(n,t);const e=Number(n.id.split(":")[0]),i=!!s.z.dokumente[e]?.pdf,l=J?.schluessel===`${s.sig}/${e}/${(t[0]?.quelle.seite??n.seite)-1}`?J.daten:null,c=t.find(r=>r.k===s.k)??null,o=(r,v)=>{if(!r||!l)return h;const w=l.px_je_pt*N;return a`<div class=${`bbox ${v}`} style=${`left:${r[0]*w}px;top:${r[1]*w}px;width:${(r[2]-r[0])*w}px;height:${(r[3]-r[1])*w}px`}></div>`},d=t.map(r=>r.quelle.bbox).filter(r=>!!r&&r.length===4),$=d.length?[Math.min(...d.map(r=>r[0])),Math.min(...d.map(r=>r[1])),Math.max(...d.map(r=>r[2])),Math.max(...d.map(r=>r[3]))]:null;return a`
    <aside class="quelle-spalte">
      <div class="saeule-rahmen">
        ${Ie(t.map(r=>({k:r.k,von:r.von,bis:r.bis,farbe:r.farbe,warn:r.offen,geprueft:r.geprueft,titel:`${U(r.von)}–${U(r.bis)} m: ${r.bodenart}${r.beschreibung?` – ${r.beschreibung}`:""}`})),{hoehe:420,gewaehlt:s.k,waehlen:r=>{s.k=r,b()}})}
      </div>
      ${i?a`<div class="pdf-rahmen">
        <div class="pdf-kopf"><b>Quelle im PDF</b> ${u("quelle")}
          <span class="fueller"></span>
          ${i?a`<button class="symbol" title="kleiner" @click=${()=>{N=Math.max(.25,N/1.4),b()}}>−</button>
            <button class="symbol" title="größer" @click=${()=>{N=Math.min(1.5,N*1.4),b()}}>+</button>`:h}
        </div>
        ${l?a`
          ${Xe($,l.px_je_pt*N)}
          <div class="pdf-seite">
            <div class="pdf-flaeche" style=${`width:${l.breite_pt*l.px_je_pt*N}px;height:${l.hoehe_pt*l.px_je_pt*N}px`}>
              <img src=${l.url} alt=${`Seite ${l.seite+1}`} draggable="false">
              ${o($,"saeule-bbox")}
              ${o(c?.quelle.bbox,"schicht-bbox")}
            </div>
          </div>`:a`<p class="leise klein">Seite wird geladen …</p>`}
      </div>`:h}
    </aside>`}let be="";function Xe(n,t){const e=`${s.bid}/${N}`;return!n||be===e?h:(requestAnimationFrame(()=>{const i=document.querySelector(".pdf-seite");i&&(i.scrollLeft=Math.max(0,n[0]*t-i.clientWidth/3),i.scrollTop=Math.max(0,n[1]*t-40),be=e)}),h)}function Ye(){const n=s.z,t=s.details.get(s.bid),e=n.bohrungen.find(c=>c.id===s.bid),i=e?Number(e.id.split(":")[0]):0,l=!n.dokumente[i]?.pdf;return a`
    <div class=${`schritt-bohrungen ${l?"ohne-pdf":""}`}>
      ${Ce()}
      ${qe()}
      <section class="bohrung-detail">
        ${e?a`
          ${Ue(e)}
          ${t?a`
            ${Ze(e,t.schichten)}
            <div class="detail-fuss">
              <button class="primaer" title="Alle Schichten dieser Bohrung als geprüft markieren und zur nächsten offenen (G)"
                @click=${_e}>✓ Alle Schichten geprüft – weiter</button>
              <button class="leise-knopf" ?disabled=${!e.schichten_geprueft}
                @click=${()=>g([{op:"bohrung_pruefen",id:e.id,wert:!1}])}>Prüfung zurücknehmen</button>
              <span class="fueller"></span>
              <button class="gefahr" @click=${()=>g([{op:"entfernen",id:e.id}])}>🗑 Aus dem Modell entfernen</button>
            </div>`:a`<p class="leise">Schichten werden geladen …</p>`}`:a`<p class="leise">Links eine Bohrung wählen.</p>`}
      </section>
      ${e&&t?Qe(e,t.schichten):a`<aside class="quelle-spalte"></aside>`}
    </div>`}const Ne=(n,t=2)=>n==null||!Number.isFinite(n)?"":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t}),S=n=>{const t=n.target.value.trim().replace(",",".");return t===""?null:Number(t)};let m=null,Q="",F="plan";function fe(n){const t=n.unterlage;return t?`${t.sha}/${t.seite}/${t.art}/${JSON.stringify(t.kalibrierung)}`:""}function Me(n){const t=n.unterlage;if(!t)return m=null;if(m&&m.schluessel===fe(n))return m;const e=t.kalibrierung,i=o=>o&&!("n"in o)?o:null,l=i(e?.massstab),c=i(e?.hoehe);return m={schluessel:fe(n),massArt:e?.massstab&&"n"in e.massstab?"n":"strecke",p1:l?{u:l.u1,v:l.v1}:null,p2:l?{u:l.u2,v:l.v2}:null,meter:l?.meter??null,n:e?.massstab&&"n"in e.massstab?e.massstab.n:null,hoeheArt:e?.hoehe?"n"in e.hoehe?"n":"strecke":"gleich",h1:c?{u:c.u1,v:c.v1}:null,h2:c?{u:c.u2,v:c.v2}:null,hoeheMeter:c?.meter??null,hoeheN:e?.hoehe&&"n"in e.hoehe?e.hoehe.n:null,bezug:e?.bezug?{u:e.bezug.u,v:e.bezug.v}:null,x:e?.bezug?.x??null,y:e?.bezug?.y??null,drehung:e?.drehung??0,epsg:e?.epsg??n.viewer.epsg??null},m}function he(n,t=!1){const e=m,i=n.unterlage;if(!e||!i)return null;let l=null;if(e.massArt==="n"&&e.n&&e.n>0&&(l={n:e.n}),e.massArt==="strecke"&&e.p1&&e.p2&&e.meter&&e.meter>0&&(l={u1:e.p1.u,v1:e.p1.v,u2:e.p2.u,v2:e.p2.v,meter:e.meter}),!l||!e.bezug||e.x===null||e.y===null)return null;let c=null;return i.art==="schnitt"&&e.hoeheArt==="n"&&e.hoeheN&&e.hoeheN>0&&(c={n:e.hoeheN}),i.art==="schnitt"&&e.hoeheArt==="strecke"&&e.h1&&e.h2&&e.hoeheMeter&&e.hoeheMeter>0&&(c={u1:e.h1.u,v1:e.h1.v,u2:e.h2.u,v2:e.h2.v,meter:e.hoeheMeter}),{massstab:l,hoehe:c,bezug:{...e.bezug,x:e.x,y:e.y},drehung:i.art==="plan"?e.drehung:0,epsg:i.art==="plan"?e.epsg:null,gesperrt:t}}function k(){const n=s.z;s.entwurf=he(n);const t=s.viewer;t&&m&&(t.editor.hilfsmarken({strecke:m.massArt==="strecke"?[m.p1,m.p2]:[],hoehe:m.hoeheArt==="strecke"?[m.h1,m.h2]:[],bezug:m.bezug}),s.entwurf&&t.editor.vorschau(s.entwurf)),b()}async function en(n){const t=s.viewer;if(!t||!m)return;Q=n,b();const e=await t.editor.bildpunktWaehlen();Q="",e&&m&&(m[n]=e),k()}async function $e(n){const t=he(s.z,n);if(!t){O("Für die Kalibrierung fehlen Maßstab oder Bezugspunkt.","warn");return}await g([{op:"kalibrierung",wert:t}])&&(s.entwurf=null,O(n?"Plan kalibriert und gesperrt – jetzt die Bohrungen ziehen.":"Kalibrierung übernommen.","ok"),await s.viewer?.ansicht(s.z?.unterlage?.art==="schnitt"?"sued":"oben"))}async function nn(n){const t=s.z.unterlage;t?.kalibrierung&&await g([{op:"kalibrierung",wert:{...t.kalibrierung,gesperrt:n}}])}async function tn(n){const t=n.target,e=t.files?.[0];if(t.value="",!e)return;const i=await B(()=>x.unterlage(s.sig,e,F,0),"Unterlage wird gelesen …");i&&(ee(i),s.entwurf=null,b(),await oe(),await s.viewer?.lageModus(!0),await s.viewer?.ansicht(i.unterlage?.art==="schnitt"?"sued":"oben"))}async function ke(n,t){const e=await B(()=>x.unterlageSeite(s.sig,n,t),"Seite wird gelesen …");e&&(ee(e),s.entwurf=null,b(),await oe(),await s.viewer?.ansicht(t==="schnitt"?"sued":"oben"))}async function an(){if(!confirm("Unterlage mit ihrer Kalibrierung entfernen? Gesetzte Bohrungen behalten ihre Lage."))return;const n=await B(()=>x.unterlageEntfernen(s.sig));n&&(ee(n),s.entwurf=null,b(),await oe())}const K=(n,t,e=!0)=>a`<details class="abschnitt" ?open=${e}><summary>${n}</summary><div class="abschnitt-inhalt">${t}</div></details>`;function j(n,t,e,i){return a`<button class=${`punkt ${Q===t?"aktiv":""} ${e?"gesetzt":""}`} ?disabled=${i}
    @click=${()=>en(t)}>${Q===t?"… im Plan klicken":e?`${n} ✓`:n}</button>`}function sn(n){const t=n.unterlage,e=Me(n),i=!!t.kalibrierung?.gesperrt,l=t.art==="plan",c=e.p1&&e.p2?Math.hypot(e.p2.u-e.p1.u,e.p2.v-e.p1.v):null,o=he(n),d=o?De(o.massstab,t.mm_pro_px):null,$=n.viewer.bohrungen.filter(r=>r.x!==null&&(l?!/Plan|Viewer/.test(r.quelle):r.gok_bekannt));return a`
    <p class=${`status ${t.kalibrierung?i?"ok":"":"warn"}`}>
      ${t.kalibrierung?a`${i?"🔒 gesperrt · ":""}${de(t)}`:"nicht kalibriert"}
      ${s.entwurf&&JSON.stringify({...s.entwurf,gesperrt:!1})!==JSON.stringify({...t.kalibrierung??{},gesperrt:!1})?a`<br><span class="leise">Vorschau: ${de(t,s.entwurf)} (noch nicht übernommen)</span>`:h}
    </p>
    ${i?a`
      <p class="leise klein">Der Plan liegt fest. Bohrungen im Viewer ziehen – ${l?"nur in x/y":"entlang der Station; die Höhe nur ohne GOK aus dem PDF"}.</p>
      <button @click=${()=>nn(!1)}>🔓 Entsperren (neu kalibrieren)</button>`:a`
      <fieldset class="gruppe">
        <legend>1 · Maßstab ${u("massstab")}</legend>
        <div class="umschalter">
          <label><input type="radio" name="massart" .checked=${e.massArt==="strecke"} @change=${()=>{e.massArt="strecke",k()}}> Strecke messen</label>
          <label><input type="radio" name="massart" .checked=${e.massArt==="n"} @change=${()=>{e.massArt="n",k()}}> 1:n eingeben</label>
        </div>
        ${e.massArt==="strecke"?a`
          <div class="zeile">${j("Punkt 1","p1",e.p1,!1)}${j("Punkt 2","p2",e.p2,!1)}</div>
          <div class="zeile">
            <span class="leise klein">${c?`gemessen ${Ne(c,0)} px`:"zwei Punkte anklicken"}</span>
            <label class="inline">wahre Länge <input type="number" step="0.01" min="0" class="kurz" .value=${f(e.meter===null?"":String(e.meter))}
              @input=${r=>{e.meter=S(r),k()}}> m</label>
          </div>`:a`
          <label class="inline">Maßstab 1: <input type="number" step="1" min="1" class="kurz" .value=${f(e.n===null?"":String(e.n))}
            @input=${r=>{e.n=S(r),k()}}></label>`}
        ${d?a`<p class="leise klein">ergibt 1:${Math.round(d).toLocaleString("de-DE")}</p>`:h}
      </fieldset>
      ${l?h:a`
        <fieldset class="gruppe">
          <legend>Höhenmaßstab ${u("hoehe")}</legend>
          <div class="umschalter">
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="gleich"} @change=${()=>{e.hoeheArt="gleich",k()}}> wie Länge</label>
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="n"} @change=${()=>{e.hoeheArt="n",k()}}> 1:n</label>
            <label><input type="radio" name="hoeheart" .checked=${e.hoeheArt==="strecke"} @change=${()=>{e.hoeheArt="strecke",k()}}> messen</label>
          </div>
          ${e.hoeheArt==="n"?a`<label class="inline">Höhe 1: <input type="number" step="1" min="1" class="kurz"
              .value=${f(e.hoeheN===null?"":String(e.hoeheN))} @input=${r=>{e.hoeheN=S(r),k()}}></label>`:h}
          ${e.hoeheArt==="strecke"?a`
            <div class="zeile">${j("Höhe oben","h1",e.h1,!1)}${j("Höhe unten","h2",e.h2,!1)}</div>
            <label class="inline">Höhenunterschied <input type="number" step="0.01" min="0" class="kurz"
              .value=${f(e.hoeheMeter===null?"":String(e.hoeheMeter))} @input=${r=>{e.hoeheMeter=S(r),k()}}> m</label>`:h}
        </fieldset>`}
      <fieldset class="gruppe">
        <legend>2 · Bezugspunkt ${u("bezug")}</legend>
        <div class="zeile">${j("Punkt im Plan wählen","bezug",e.bezug,!1)}</div>
        <div class="zeile">
          <label class="feld schmal"><span>${l?"Rechtswert":"Station [m]"}</span>
            <input type="number" step="0.01" .value=${f(e.x===null?"":String(e.x))} @input=${r=>{e.x=S(r),k()}}></label>
          <label class="feld schmal"><span>${l?"Hochwert":"Höhe [m NHN]"}</span>
            <input type="number" step="0.01" .value=${f(e.y===null?"":String(e.y))} @input=${r=>{e.y=S(r),k()}}></label>
        </div>
        ${$.length?a`
          <label class="inline klein">oder von Bohrung
            <select @change=${r=>{const v=n.viewer.bohrungen.find(w=>w.id===r.target.value);v&&(e.x=v.x,e.y=l?v.y:v.gok,k())}}>
              <option value="">–</option>
              ${$.map(r=>a`<option value=${r.id}>${r.code}</option>`)}
            </select></label>`:h}
      </fieldset>
      ${l?a`
        <fieldset class="gruppe">
          <legend>3 · Drehung ${u("drehung")}</legend>
          <div class="zeile">
            <label class="inline"><input type="number" step="0.1" class="kurz" .value=${f(String(e.drehung))}
              @input=${r=>{e.drehung=S(r)??0,k()}}> ° gegen den Uhrzeigersinn</label>
          </div>
          <label class="inline">EPSG ${u("epsg")} <input type="number" step="1" class="kurz" .value=${f(e.epsg===null?"":String(e.epsg))}
            @input=${r=>{e.epsg=S(r),k()}}></label>
        </fieldset>`:h}
      <div class="zeile knopfzeile">
        <button ?disabled=${!o} @click=${()=>$e(!1)}>Übernehmen</button>
        <button class="primaer" ?disabled=${!o} @click=${()=>$e(!0)}>🔒 Übernehmen und sperren</button>
        ${u("sperren")}
      </div>
      ${t.kalibrierung?a`<button class="link klein" @click=${()=>g([{op:"kalibrierung",wert:null}])}>Kalibrierung zurücksetzen</button>`:h}`}`}function ln(n){const t=n.unterlage;return t?a`
    <p><b>${t.name}</b> <span class="leise">· ${t.art==="plan"?"Lageplan":"Längsschnitt"}</span></p>
    <div class="zeile">
      ${(t.seiten??1)>1?a`<label class="inline">Seite <select @change=${e=>ke(Number(e.target.value),t.art)}>
          ${Array.from({length:t.seiten},(e,i)=>a`<option value=${i} .selected=${i===t.seite}>${i+1}</option>`)}
        </select></label>`:h}
      <label class="inline">Ansicht <select @change=${e=>ke(t.seite,e.target.value)}>
        <option value="plan" .selected=${t.art==="plan"}>Lageplan</option>
        <option value="schnitt" .selected=${t.art==="schnitt"}>Längsschnitt</option>
      </select></label>
    </div>
    <label class="inline">Deckkraft ${u("deckkraft")}
      <input type="range" min="0.1" max="1" step="0.05" .value=${String(s.viewer?.editor.deckkraft??.85)}
        @input=${e=>{s.viewer&&(s.viewer.editor.deckkraft=Number(e.target.value),s.viewer.editor.bildSichtbarkeit())}}></label>
    <button class="link klein" @click=${an}>Unterlage entfernen</button>`:a`
      <p class="leise klein">Lageplan (von oben) oder Längsschnitt (von der Seite) als PDF – er liegt im Viewer unter den Bohrungen.</p>
      <div class="umschalter">
        <label><input type="radio" name="neueart" .checked=${F==="plan"} @change=${()=>{F="plan"}}> Lageplan</label>
        <label><input type="radio" name="neueart" .checked=${F==="schnitt"} @change=${()=>{F="schnitt"}}> Längsschnitt</label>
      </div>
      <label class="datei-knopf"><input type="file" accept=".pdf,application/pdf" @change=${tn}>PDF wählen …</label>`}function rn(n){const t=n.unterlage,e=!t||!!t.kalibrierung?.gesperrt,i=n.viewer.bohrungen.filter(c=>c.x===null),l=n.lage_modus==="reihe";return a`
    ${e?h:a`<p class="warnung">Erst kalibrieren und sperren (🔒) – dann die Bohrungen ziehen.</p>`}
    ${i.length?a`
      <p class="klein">Ohne Lage (${i.length}) – in den Viewer ziehen ${u("ohne_lage")}</p>
      <div class="parkplatz">
        ${i.map(c=>a`<span class="park ${e?"":"gesperrt"}" title="In den Viewer ziehen"
          @pointerdown=${o=>s.viewer?.editor.ziehenStart(o,c.id,!0)}>${c.code}</span>`)}
      </div>`:a`<p class="leise klein">Alle Bohrungen im Modell haben eine Lage.</p>`}
    ${l?cn(n):h}`}function cn(n){const t=n.reihe.map(i=>i.id),e=(i,l)=>{const c=[...t],[o]=c.splice(i,1);c.splice(Math.max(0,Math.min(c.length,i+l)),0,o),g([{op:"reihe",reihenfolge:c}],{leise:!0})};return a`
    <div class="zeile">
      <label class="inline">Standardabstand ${u("standardabstand")}
        <input type="number" step="1" min="1" class="kurz" .value=${f(String(n.reihe_standard))}
          @change=${i=>g([{op:"reihe",standard:S(i)}])}> m</label>
    </div>
    <table class="tabelle kompakt reihe">
      <thead><tr><th></th><th>Bohrung</th><th>Abstand [m] ${u("reihe")}</th><th>Station [m]</th></tr></thead>
      <tbody>
        ${n.reihe.map((i,l)=>a`
          <tr>
            <td class="pfeile"><button class="symbol" ?disabled=${l===0} title="nach vorn" @click=${()=>e(l,-1)}>▲</button><button class="symbol"
              ?disabled=${l===t.length-1} title="nach hinten" @click=${()=>e(l,1)}>▼</button></td>
            <td>${i.code}</td>
            <td><input type="number" step="0.1" min="0" class="kurz" ?disabled=${l===0} .value=${f(i.abstand===null?"":String(i.abstand))}
              @change=${c=>g([{op:"reihe",abstand:{[i.id]:S(c)}}],{leise:!0})}></td>
            <td><input type="number" step="0.1" class="kurz" .value=${f(String(i.station))} title=${i.quelle_text}
              @change=${c=>g([{op:"reihe",station:{[i.id]:S(c)}}],{leise:!0})}></td>
          </tr>`)}
      </tbody>
    </table>`}function on(n){const t=s.viewer;t&&(!n.unterlage||n.unterlage.kalibrierung?.gesperrt||!m?t.editor.hilfsmarken({}):t.editor.hilfsmarken({strecke:m.massArt==="strecke"?[m.p1,m.p2]:[],hoehe:m.hoeheArt==="strecke"?[m.h1,m.h2]:[],bezug:m.bezug}))}function hn(){const n=s.z;return Me(n),on(n),a`
    <div class="app-panel links">
      ${K(a`Lage der Bohrungen ${u("lage_art")}`,a`
        <div class="umschalter">
          <label><input type="radio" name="lagemodus" .checked=${n.lage_modus==="koordinaten"}
            @change=${()=>g([{op:"lage_modus",wert:"koordinaten"}])}> Koordinaten (Lageplan)</label>
          <label><input type="radio" name="lagemodus" .checked=${n.lage_modus==="reihe"}
            @change=${()=>g([{op:"lage_modus",wert:"reihe"}])}> Reihe (Längsschnitt)</label>
        </div>`)}
      ${K(a`Unterlage ${u("unterlage")}`,ln(n))}
      ${n.unterlage?K(a`Kalibrieren`,sn(n)):h}
      ${K(a`Bohrungen setzen`,rn(n))}
      ${K(a`Darstellung`,a`
        <label class="inline">Ø Bohrsäulen ${u("durchmesser")}
          <input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${Ne(n.durchmesser_auto,1)}`}
            .value=${f(n.durchmesser===null?"":String(n.durchmesser))}
            @change=${t=>g([{op:"durchmesser",wert:S(t)}])}> m</label>
        <p class="leise klein">Je Bohrung im Schritt Bohrungen (Ø Säule). Leer = automatisch nach Modellgröße.</p>`,!1)}
      ${n.hinweise.length?a`<div class="hinweisliste">${n.hinweise.map(t=>a`<p class="klein">ℹ ${t}</p>`)}</div>`:h}
    </div>`}const D=(n,t=1)=>n==null?"–":n.toLocaleString("de-DE",{minimumFractionDigits:t,maximumFractionDigits:t});let E="",ie=null,ve="";function un(){const n=s.z.einstellungen,t=(l,c)=>g([{op:"einstellungen",[l]:c}]),e=(l,c,o,d,$)=>{const r=n[l];return a`
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${r===null} @change=${v=>t(l,v.target.checked?null:d)}> ${c} automatisch</label>${u($)}
        ${r===null?h:a`<input type="number" step="any" class="kurz" .value=${f(String(r))}
          @change=${v=>t(l,Number(v.target.value))}> ${o}`}
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
        <label class="inline"><input type="checkbox" .checked=${n.gok_relativ} @change=${l=>t("gok_relativ",l.target.checked)}> fehlende GOK: Gelände = 0 m</label>${u("gok_relativ")}
      </div>
      ${i.raster_m!==void 0?a`<p class="leise klein">gerechnet: Puffer ${D(Number(i.puffer_m),0)} m · Raster ${D(Number(i.raster_m))} m ·
        Basis ${D(Number(i.basis_nhn),2)} m NHN · Fläche ${D(Number(i.flaeche_m2)/1e4,2)} ha</p>`:h}
    </section>`}function dn(){const n=s.modell?.bericht;if(!n)return h;const t=s.z.vorgabe??n.vorlage_einheiten,e=JSON.stringify(t);(!ie||ve!==e)&&(ie=t.map(c=>({name:c.name,bodenarten:c.bodenarten.join(", ")})),ve=e);const i=ie,l=()=>g([{op:"vorgabe",wert:i.filter(c=>c.name.trim()).map(c=>({name:c.name.trim(),bodenarten:c.bodenarten.split(",").map(o=>o.trim()).filter(Boolean)}))}]);return a`
    <section class="karte">
      <h3>Einheiten festlegen ${u("einheiten")}</h3>
      <p class="leise klein">${s.z.vorgabe?"Vorgegeben (eigene Einheiten).":"Automatisch korreliert – hier umbenennen oder Bodenarten zusammenlegen."}</p>
      <table class="tabelle kompakt vorgabe">
        <colgroup><col class="pfeil"><col><col><col class="weg"></colgroup>
        <thead><tr><th></th><th>Einheit</th><th>Bodenarten (mit Komma)</th><th></th></tr></thead>
        <tbody>
          ${i.map((c,o)=>a`
            <tr>
              <td class="pfeile"><button class="symbol" ?disabled=${o===0} @click=${()=>{i.splice(o-1,0,...i.splice(o,1)),b()}}>▲</button><button
                class="symbol" ?disabled=${o===i.length-1} @click=${()=>{i.splice(o+1,0,...i.splice(o,1)),b()}}>▼</button></td>
              <td><input .value=${f(c.name)} @input=${d=>{c.name=d.target.value}}></td>
              <td><input .value=${f(c.bodenarten)} @input=${d=>{c.bodenarten=d.target.value}}></td>
              <td><button class="symbol" title="Zeile löschen" @click=${()=>{i.splice(o,1),b()}}>✕</button></td>
            </tr>`)}
        </tbody>
      </table>
      <div class="zeile knopfzeile">
        <button class="link" @click=${()=>{i.push({name:"",bodenarten:""}),b()}}>+ Zeile</button>
        <span class="fueller"></span>
        <button ?disabled=${!s.z.vorgabe} @click=${()=>g([{op:"vorgabe",wert:null}])}>Automatisch korrelieren</button>
        <button class="primaer" @click=${l}>Mit diesen Einheiten rechnen</button>
      </div>
    </section>`}function gn(){const n=s.modell,t=n?.bericht,e=t?.einheiten.find(i=>i.name===E);return a`
    <div class="schritt-einheiten">
      <div class="spalte">
        ${un()}
        ${dn()}
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
                  <tr class=${i.name===E?"gewaehlt":""} @click=${()=>{E=E===i.name?"":i.name,b()}}>
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
            <div class="profil-scroll">${Te(t,{hoehe:380,gewaehlt:E,waehlen:i=>{E=i,b()}})}</div>
          </section>
          ${e?a`
            <section class="karte">
              <h3><span class="farbfeld" style=${`background:${e.farbe}`}></span> ${e.name}: Beschreibungen aus dem PDF</h3>
              <table class="tabelle kompakt">
                <thead><tr><th>Bohrung</th><th>Tiefe [m]</th><th>Bodenart</th><th>Beschreibung</th></tr></thead>
                <tbody>${e.schichten.map(i=>a`
                  <tr><td>${i.bohrung}</td><td class="zahl">${D(i.von,2)}–${D(i.bis,2)}</td><td>${i.bodenart??"unklassifiziert"}</td>
                    <td>${i.beschreibung||a`<span class="leise">–</span>`}</td></tr>`)}</tbody>
              </table>
            </section>`:h}`:h}
      </div>
    </div>`}let X="";async function pn(){const n=await B(()=>x.einchecken(s.sig,X));n&&(ee(n.zustand),X="",O(`Eingecheckt: v${n.eintrag.nr} · ${n.eintrag.stand.bohrungen[0]}/${n.eintrag.stand.bohrungen[1]} Bohrungen geprüft`,"ok"),b())}function mn(){const n=s.z,t=s.modell,e=t?.bericht,i=n.pruefstand,l=n.eincheckungen[n.eincheckungen.length-1],c=[["ifc","Baugrundmodell (IFC 4.3)"],["bericht","Prüfbericht (JSON)"],["einheiten","Einheiten-Vorlage (JSON)"],["extraktion","Extraktion (JSON)"],["eingabe","Modell-Eingabe mit Korrekturen (JSON)"],["projekt","Projektstand (JSON)"]];return a`
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
          <button ?disabled=${s.rechnet} @click=${()=>Le()}>Neu rechnen</button>
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
        <p class=${`klein ${l&&!n.seit_einchecken_geaendert?"ok":"warn"}`}>
          ${l?`Eingecheckt: ${n.eingecheckt}${n.seit_einchecken_geaendert?" · seitdem geändert":""}`:"noch nicht eingecheckt"}</p>
        <div class="zeile">
          <input class="breit" placeholder="Kommentar (z. B. BK1–BK5 mit Anlage 2 verglichen)" .value=${X}
            @input=${o=>{X=o.target.value}}>
        </div>
        <div class="zeile"><button class="primaer" @click=${pn}>✓ Stand einchecken</button>${u("einchecken")}</div>
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
          ${c.map(([o,d])=>a`<a class=${`knopf ${o==="ifc"?"primaer":""}`} href=${x.exportUrl(s.sig,o)}
            download>${d}</a>`)}
        </div>
      </section>

      ${t&&(t.hinweise.length||t.nicht_im_modell.length)?a`
        <section class="abschnitt-flach">
          <h3>Hinweise</h3>
          ${t.nicht_im_modell.length?a`<p class="klein"><b>Nicht im Modell:</b> ${t.nicht_im_modell.map(o=>`${o.code} (${o.grund})`).join(", ")}</p>`:h}
          ${t.hinweise.map(o=>a`<p class="klein">ℹ ${o}</p>`)}
        </section>`:h}
    </div>`}const we={gutachten:"",bohrungen:"Weiter: Lage",lage:"Weiter: Einheiten",einheiten:"Weiter: Modell",modell:""};function bn(n){const t=s.z;if(!t)return"";const e=t.pruefstand;return n==="gutachten"?"ok":n==="bohrungen"?e.unklassifiziert_offen?"warn":e.bohrungen[0]===e.bohrungen[1]&&e.bohrungen[1]?"ok":"":n==="lage"?t.viewer.bohrungen.filter(l=>l.x===null).length?"warn":"ok":n==="einheiten"||n==="modell"?s.modell?.fehler?"warn":s.modell?.bericht?"ok":"":""}function fn(){const n=s.z;return a`
    <header class="kopf">
      <div class="marke" @click=${()=>M("gutachten")} title="Start">
        <span class="logo">⛰</span>
        <span><b>Geo_Agent</b> · Baugrundmodell</span>
      </div>
      <nav class="schritte" aria-label="Schritte">
        ${q.map(t=>{const e=t.id!=="gutachten"&&!n,i=bn(t.id);return a`
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
            <div class="menue-inhalt" @click=${$n}>
              <button @click=${()=>M("gutachten")}>Anderes Projekt öffnen</button>
              <button @click=${kn}>Alle Korrekturen verwerfen …</button>
              <a href="viewer.html" target="_blank" rel="noopener">Viewer allein öffnen</a>
            </div>
          </details>`:h}
      </div>
    </header>`}function $n(n){n.currentTarget.closest("details")?.removeAttribute("open")}document.addEventListener("click",n=>{for(const t of document.querySelectorAll("details.menue[open]"))t.contains(n.target)||t.removeAttribute("open")});async function kn(){if(!s.sig||!confirm("Alle Korrekturen, Lagen, Prüfhaken und Eincheckungen dieses Projekts verwerfen?"))return;await B(()=>x.zuruecksetzen(s.sig))&&await G(s.sig,"bohrungen")}function vn(){if(s.schritt==="gutachten")return h;const n=q.findIndex(l=>l.id===s.schritt),t=q[n-1],e=q[n+1],i=s.z?.pruefstand;return a`
    <footer class="fuss">
      ${t?a`<button @click=${()=>M(t.id)}>← ${t.titel}</button>`:h}
      <span class="fuss-status">${i?`${i.bohrungen[0]}/${i.bohrungen[1]} Bohrungen · ${i.schichten[0]}/${i.schichten[1]} Schichten geprüft`:""}
        ${i?.unklassifiziert_offen?a` · <span class="warnung">⚠ ${i.unklassifiziert_offen} nicht klassifiziert</span>`:h}</span>
      <span class="fueller"></span>
      ${e&&we[s.schritt]?a`<button class="primaer" @click=${()=>M(e.id)}>${we[s.schritt]} →</button>`:h}
    </footer>`}function wn(){return s.schritt==="gutachten"||!s.z?Ge():s.schritt==="bohrungen"?Ye():s.schritt==="lage"?hn():s.schritt==="einheiten"?gn():mn()}function zn(){return a`
    ${fn()}
    <main class=${`inhalt schritt-${s.schritt}`}>
      <section id="schritt" class="schritt">${wn()}</section>
    </main>
    ${vn()}
    <div class="meldungen" aria-live="polite">
      ${s.meldungen.map(n=>a`<div class=${`meldung ${n.art}`}>${n.text}</div>`)}
    </div>
    ${s.beschaeftigt?a`<div class="beschaeftigt"><div class="kreisel"></div><span>${s.beschaeftigt}</span></div>`:h}`}const ze=document.getElementById("app");let L=null;function yn(){Ee(zn(),ze);const n=ze.querySelector("main");L||(L=document.createElement("div"),L.id="buehne",L.className="buehne"),L.parentElement!==n&&n.append(L),document.body.dataset.schritt=s.schritt}Ke(yn);async function Pe(){const[n,t,e]=location.hash.replace(/^#\/?/,"").split("/").map(decodeURIComponent);if(n&&n!==s.sig){if(await G(n,t||void 0),e&&s.schritt==="bohrungen"){const{bohrungWaehlen:i}=await Ae(async()=>{const{bohrungWaehlen:l}=await import("./store-BI5Rw7m0.js").then(c=>c.j);return{bohrungWaehlen:l}},__vite__mapDeps([0,1]),import.meta.url);await i(e)}}else n||await M("gutachten")}window.addEventListener("hashchange",()=>void Pe());s.info=await B(()=>x.info())??null;b();await ye();await Pe();window.app=s;
