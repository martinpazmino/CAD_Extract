---
title: "22 En línea: despliegue desde GitHub y por qué no Vercel"
date: 2026-10-29
tags: [despliegue, docker, render, vercel, seguridad, agpl, ci]
aliases: [Despliegue, Deploy, En línea, Online]
---

# 22 En línea: despliegue desde GitHub y por qué no Vercel

**Conclusión:** la app entera va en **un contenedor** construido desde este mismo repositorio
([`Dockerfile`](../Dockerfile)): servidor FastAPI, página compilada y extracción. Con
[`render.yaml`](../render.yaml) queda lista para Render:
- blueprint con un clic;
- disco en `/data`;
- servidor en Fráncfort;
- contraseña.

Otras plataformas de contenedores sirven igual (§4). **Vercel no sirve para esta arquitectura**:
limita cada petición a 4,5 MB, no tiene disco y no deja procesos en segundo plano. Allí sólo podría ir
la página estática (§2).

## 1. Qué necesita la app en un servidor

| Necesidad | Por qué | Dónde |
|---|---|---|
| Subidas de PDF grandes | Un Gutachten con anexos y planos pesa a menudo decenas de MB | Límite `GEO_AGENT_MAX_MB` (200) |
| Disco que persista | Cada proyecto (estado JSON, PDF, planos, IFC) se guarda como archivos | `GEO_AGENT_ARBEIT` → `/data` |
| Un proceso que siga vivo | La extracción corre en un hilo y el estado de los trabajos está en memoria | `server/` |
| Unos 300 MB de RAM sin OCR | Medido (§6) | |
| **Una sola instancia** | Estado en memoria y disco local: con dos instancias cada una vería otros proyectos | No escalar horizontalmente |

## 2. ¿Vercel?

Vercel aloja sitios estáticos y **funciones** (serverless). Sus límites, consultados el 2026-10-29:

| Límite de Vercel | Valor | Consecuencia para GeoIM |
|---|---|---|
| Cuerpo de la petición o la respuesta de una función | **4,5 MB**, en todos los planes. Fuentes: [límites de las funciones](https://vercel.com/docs/functions/limitations); [foro: 413 Payload Too Large](https://community.vercel.com/t/413-payload-too-large/218) | Un Gutachten no se puede subir. Habría que subirlo directamente a Vercel Blob ([client upload](https://vercel.com/docs/vercel-blob)) y reescribir la subida |
| Disco | Ninguno persistente: lo escrito desaparece con la instancia | Los proyectos se perderían. Haría falta Blob + base de datos |
| Duración | 300 s por defecto; hasta 800 s en Pro/Enterprise con Fluid compute ([duración](https://vercel.com/docs/functions/configuring-functions/duration)) | El hilo de extracción no sobrevive a la respuesta. Haría falta una cola de trabajos |
| Tamaño del paquete Python | 500 MB sin comprimir ([runtime Python](https://vercel.com/docs/functions/runtimes/python)); hasta 5 GB en beta ([changelog](https://vercel.com/changelog/bun-runtime-now-supports-large-functions-and-extended-max-duration)) | Las dependencias ocupan unos 690 MB (§6) |

Para llevar GeoIM a Vercel habría que rehacer la subida, el almacenamiento, los trabajos y el empaquetado,
y la app seguiría siendo la misma. No compensa.

Lo único que funciona allí sin cambios es la **página estática** `apps/web/dist`. Sin la API sólo sirve
el visor (`viewer.html?ifc=<url de un IFC>`), por ejemplo como demo pública de un modelo.

## 3. Render paso a paso (recomendado)

1. **Llevar los archivos a `main`.** `render.yaml` y `Dockerfile` tienen que estar en `main` (merge del
   pull request): el blueprint despliega `main`.
2. **Crear el blueprint.** En [render.com](https://render.com), entrar con GitHub → *New → Blueprint* →
   repositorio `martinpazmino/GeoIM`. Si Render no lo ve, darle acceso en GitHub (*Configure GitHub
   App*). El botón *Deploy to Render* del README hace lo mismo.
3. **Revisar lo que crea.** Render lee `render.yaml`:
   - servicio web `geoim` (Docker), región `frankfurt`, plan `starter`;
   - disco `geoim-daten` de 5 GB en `/data`;
   - comprobación de salud en `/gesund`.
4. **Poner la contraseña.** Render pide `GEO_AGENT_PASSWORT`, que no se guarda en el repositorio.
   Elegir una contraseña larga y compartirla sólo con el equipo.
5. **Aplicar y esperar.** *Apply* lanza el primer build. La URL queda como `https://geoim-….onrender.com`
   (se puede añadir un dominio propio).
6. **Entrar.** Al abrir la URL, el navegador pide usuario y contraseña. El usuario puede ser
   cualquiera, salvo que se fije `GEO_AGENT_BENUTZER`.
7. **Actualizar.** Cada push a `main` vuelve a construir y desplegar. Los proyectos de `/data` se
   conservan.

Costes **[a verificar en render.com/pricing]**:

| Plan | Recursos | Precio | Para qué |
|---|---|---|---|
| `starter` | 512 MB, 0,5 CPU | unos 7 $/mes | Sin OCR |
| `standard` | 2 GB | unos 25 $/mes | OCR de escaneos o Gutachten muy grandes |
| Disco | 5 GB | unos 1,25 $/mes (0,25 $/GB) | Proyectos |
| `free` | | 0 $ | Sólo una demo: no admite disco (los proyectos se pierden) y se duerme sin uso |

Si la plataforma dice que falta memoria (el servicio se reinicia durante una extracción), subir de plan.

## 4. Otras plataformas: mismo repositorio, mismo Dockerfile

| Plataforma | Cómo | Ojo |
|---|---|---|
| **Railway** | *New Project → Deploy from GitHub repo*. Detecta el `Dockerfile`. Añadir un *Volume* en `/data` y la variable `GEO_AGENT_PASSWORT` | Pone `PORT` sola |
| **Fly.io** | `fly launch` crea `fly.toml`; región `fra`. `fly volumes create` y montarlo en `/data`. `fly secrets set GEO_AGENT_PASSWORT=…` | El despliegue desde GitHub va por una GitHub Action |
| **Servidor propio** (VPS, servidor de la empresa) | `docker run -d -p 8500:8500 -e GEO_AGENT_PASSWORT=… -v geoim-daten:/data geoim`, con Caddy o nginx delante para HTTPS | Control total; los datos se quedan en casa (RGPD) |
| Google Cloud Run | Build desde GitHub | Sin disco persistente por defecto y CPU sólo durante las peticiones **[a verificar]**: no encaja con el hilo de extracción |
| Hugging Face Spaces (Docker) | Space aparte con `app_port: 8500` | Repositorio propio en HF; no apto para Gutachten confidenciales en un Space público |

## 5. Variables de entorno

| Variable | Por defecto | Para qué |
|---|---|---|
| `PORT` | 8500 | Puerto. Las plataformas lo ponen solas |
| `GEO_AGENT_HOST` | `127.0.0.1` (en el contenedor `0.0.0.0`) | Interfaz de red. Si no es local y falta la contraseña, el servidor avisa al arrancar |
| `GEO_AGENT_PASSWORT` | — | Contraseña (HTTP Basic) para todo salvo `/gesund`. **Sin ella la app queda abierta** |
| `GEO_AGENT_BENUTZER` | — (cualquier usuario) | Usuario obligatorio |
| `GEO_AGENT_MAX_MB` | 200 | Tamaño máximo de una petición. Por encima responde 413 |
| `GEO_AGENT_ARBEIT` | Carpeta temporal `geo_agent` (en el contenedor `/data`) | Proyectos. En línea **siempre** en un disco persistente |
| `GEO_AGENT_QUELLCODE` | `https://github.com/martinpazmino/GeoIM` | Enlace *Quellcode* (AGPL § 13). Un fork con cambios pone aquí su repositorio |

## 6. Memoria y tamaño (medidos)

Imagen sin OCR, en la sesión del 2026-10-29:

| Medida | Valor |
|---|---|
| Imagen | 1,15 GB |
| Dependencias Python | 686 MB: ifcopenshell 203, PyMuPDF 116, SciPy 109, onnxruntime 68 (lo trae PyMuPDF 2.0) |
| Memoria en reposo | 98 MB |
| Memoria tras el modelo de la trasse de 6 km | 161 MB |
| Memoria tras extraer el PDF sintético | 290 MB |

Con OCR se añaden OpenCV y los modelos de RapidOCR. El OCR de páginas grandes puede necesitar más de
1 GB ([X7](16_lecciones_aprendidas.md#x-entorno-de-trabajo)), así que con escaneos conviene un plan de
2 GB.

## 7. Seguridad, datos y licencia

- **HTTPS** lo pone la plataforma (Render, Railway, Fly). En un servidor propio, con Caddy o nginx
  delante.
- **Una contraseña para todo el equipo.** No hay usuarios ni permisos por proyecto: quien la tiene ve
  todos los proyectos. Para clientes distintos, una instancia por cliente. Más adelante, Supabase
  con RLS ([arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)).
- **`/gesund`** responde sin contraseña y sólo devuelve la versión.
- **Gutachten confidenciales:**
  - región UE (Fráncfort);
  - contrato de encargo (AVV/DPA) con el proveedor;
  - requisitos de [14 §6](14_licencias_terceros.md#6-otros-requisitos-cuando-lleguen-terceros).
- **Copias de seguridad:** el disco de la plataforma no sustituye una copia propia. Exportar los
  proyectos importantes (IFC, JSON).
- **AGPL § 13:** el enlace *Quellcode* debe seguir visible y llevar al código de la versión
  desplegada. Está en el pie de la primera página y en el menú ⋯. Detalles en
  [THIRD_PARTY_LICENSES](../THIRD_PARTY_LICENSES.md) y [14](14_licencias_terceros.md).

## 8. Dependencias y versiones

- `requirements-server.txt`: sólo lo que la app necesita en línea.
- `requirements.txt`: añade Streamlit (Excel v1) y las pruebas.
- `requirements-ocr.txt`: el OCR.
- `constraints.txt`: versiones exactas con las que se construyó y probó la imagen (Python 3.13). El
  `Dockerfile` y la CI instalan con `-c constraints.txt`, así que un despliegue no cambia de versión
  por sorpresa.

Para actualizar las versiones:

```bash
python3.13 -m venv /tmp/neu && /tmp/neu/bin/pip install -r requirements-server.txt -r requirements-ocr.txt
/tmp/neu/bin/pip freeze          # → constraints.txt (la parte de OCR en su sección)
pytest tests && (cd services/modeler && pytest tests)
docker build -t geoim .          # y check_app.mjs contra el contenedor (§10)
```

## 9. Pruebas automáticas (CI)

[`.github/workflows/pruefungen.yml`](../.github/workflows/pruefungen.yml) corre en cada push y pull request:

| Job | Qué comprueba |
|---|---|
| Python | `pytest tests` (proyecto, API, acceso) y el modelador con sus normas |
| Oberfläche | `npm ci && npm run build`: la página compila. `dist` sigue viniendo del repositorio |
| Container | La imagen **con OCR** se construye y arranca con contraseña: `/gesund`, 401 sin contraseña, 200 con ella, `import cv2, rapidocr_onnxruntime` |
| Ende zu Ende | Sólo a mano (*Run workflow*): `scripts/check_app.mjs` con Playwright; las capturas quedan como artefacto |

## 10. Qué está probado

Probado en la sesión, con la imagen sin OCR:
- la imagen se construye y arranca con el usuario 1000;
- un volumen de root se cambia de dueño al arrancar;
- 401 sin contraseña, 200 con ella;
- `/gesund` responde;
- el modelo de la demo sale con 7 unidades y sólidos cerrados;
- **28/28 comprobaciones de `check_app.mjs` contra el contenedor**.

**No probado aquí** (la red de la sesión bloquea deb.debian.org y render.com,
[X25](16_lecciones_aprendidas.md#x-entorno-de-trabajo)):
- la instalación del OCR con apt: la prueba el job *Container* de la CI;
- el blueprint en Render: se verá en el primer despliegue.

Construir en local:

```bash
docker build -t geoim .                          # con OCR
docker build -t geoim --build-arg OCR=0 .        # sin OCR (más pequeña, sin paquetes del sistema)
docker run --rm -p 8500:8500 -e GEO_AGENT_PASSWORT=prueba -v "$(mktemp -d)":/data geoim
python scripts/testplan.py planes
GEO_AGENT_PASSWORT=prueba node scripts/check_app.mjs http://localhost:8500 planes capturas
```

`check_app.mjs` se identifica con la misma contraseña. Necesita un **disco vacío**: crea proyectos y
cambia los ejemplos, así que no se debe lanzar contra el despliegue real.

Up: [Índice](README.md)

Related: [21 App por pasos](21_app_schritte_normen.md) · [14 Licencias](14_licencias_terceros.md) · [11 Decisiones](11_decisiones.md) · [16 Lecciones](16_lecciones_aprendidas.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
