---
title: "22 Online: deployment from GitHub, the free option and why not Vercel"
date: 2026-10-29
tags: [deployment, docker, render, cloudflare, vercel, security, agpl, ci]
aliases: [Deployment, Deploy, Online, Free hosting]
---

# 22 Online: deployment from GitHub, the free option and why not Vercel

**Conclusion:**

- **Free:** the app runs on your own PC and a **Cloudflare Quick Tunnel** gives it a public https
  address (`start_online.bat`). The Gutachten stay on the PC. The address only lives while the PC
  and the window are running (§3).
- **Permanent service:** the whole app goes into **one container** built from this repository
  ([`Dockerfile`](../Dockerfile)): FastAPI server, compiled page and extraction. With
  [`render.yaml`](../render.yaml) it is ready for Render: one-click blueprint, disk at `/data`,
  servers in Frankfurt, password (§4). Other container platforms work the same way (§5).
- **Vercel does not fit this architecture**: it limits every request to 4.5 MB, has no disk and runs
  no background work. Only the static page could go there (§2).

## 1. What the app needs on a server

| Need | Why | Where |
|---|---|---|
| Uploads of large PDFs | A Gutachten with annexes and plans often weighs tens of MB | Limit `GEO_AGENT_MAX_MB` (200) |
| A disk that persists | Each project (JSON state, PDF, plans, IFC) is stored as files | `GEO_AGENT_ARBEIT` → `/data` |
| A process that stays alive | The extraction runs in a thread and the job state is in memory | `server/` |
| About 300 MB of RAM without OCR | Measured (§7) | |
| **A single instance** | State in memory and on the local disk: with two instances each one would see other projects | Do not scale horizontally |

## 2. Vercel?

Vercel hosts static sites and **functions** (serverless). Its limits, checked on 2026-10-29:

| Vercel limit | Value | Consequence for GroundTwin |
|---|---|---|
| Body of a function's request or response | **4.5 MB**, on all plans. Sources: [function limits](https://vercel.com/docs/functions/limitations); [forum: 413 Payload Too Large](https://community.vercel.com/t/413-payload-too-large/218) | A Gutachten cannot be uploaded. It would have to go straight to Vercel Blob ([client upload](https://vercel.com/docs/vercel-blob)) and the upload be rewritten |
| Disk | None that persists: what is written disappears with the instance | The projects would be lost. Blob + a database would be needed |
| Duration | 300 s by default; up to 800 s on Pro/Enterprise with Fluid compute ([duration](https://vercel.com/docs/functions/configuring-functions/duration)) | The extraction thread does not survive the response. A job queue would be needed |
| Size of the Python bundle | 500 MB uncompressed ([Python runtime](https://vercel.com/docs/functions/runtimes/python)); up to 5 GB in beta ([changelog](https://vercel.com/changelog/bun-runtime-now-supports-large-functions-and-extended-max-duration)) | The dependencies take about 690 MB (§7) |

Moving GroundTwin to Vercel would mean redoing the upload, the storage, the jobs and the packaging,
and the app would still be the same. It is not worth it.

The only thing that works there unchanged is the **static page** `apps/web/dist`. Without the API
only the viewer is useful (`viewer.html?ifc=<URL of an IFC>`), for example as a public demo of a
model.

## 3. Free: your own PC + Cloudflare Tunnel

The app runs on your computer as usual; [`scripts/online.py`](../scripts/online.py) starts it **with
a password** and asks `cloudflared` for a **Quick Tunnel**: an https address under
`trycloudflare.com` that forwards to this PC. No Cloudflare account is needed.

### 3.1 Steps (Windows)

1. **Once:** run [`start.bat`](../start.bat) (it installs everything) and install `cloudflared`:

   ```bat
   winget install --id Cloudflare.cloudflared
   ```

   Afterwards open a new window, so that the new program is found.
2. **Go online:** double click on [`start_online.bat`](../start_online.bat). The window shows:

   ```
   GroundTwin ist online:  https://<random-words>.trycloudflare.com
   Benutzer: beliebig      Passwort: <generated>
   ```

3. **Share** address and password only with people who may see the Gutachten. The browser asks for
   them; any user name works.
4. **Stop:** Ctrl+C or close the window. The address is gone; the next start gives a new address and
   a new password. To keep the password: `start_online.bat --passwort <MyPassword>`.

Other systems: `python scripts/online.py [--port 8500] [--passwort …] [--arbeit <folder>]`, with
`cloudflared` from `brew install cloudflared` (macOS) or the
[Cloudflare downloads](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)
(Linux).

The script **refuses** to put a server online that is already running on the port (for example
`start.bat`, which has no password), and it never starts without a password.

### 3.2 What to know

- **The PC must stay on** (and not go to sleep). The app uses the PC's own CPU and RAM, so OCR of
  scans works as it does locally.
- **The address changes on every start.** Cloudflare offers Quick Tunnels for testing and
  development: no uptime guarantee and at most 200 requests in flight
  ([Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)).
  For a fixed address you need a free Cloudflare account **and your own domain** (named tunnel).
- **Uploads above 100 MB** are rejected by Cloudflare on the free plan (according to users' reports;
  not confirmed on an official page). Larger PDFs: upload them on the PC itself at
  `http://localhost:8500`.
- **The data stays on the PC**, in the work folder (`%TEMP%\geo_agent` unless `--arbeit` is given).
  Export important projects (IFC, JSON); the temp folder can be cleaned by Windows.
- **On a company PC, ask IT first.** A tunnel opens a way from the internet to an app inside the
  company network; many IT policies forbid that.
- **Inside the company network** no tunnel is needed: `python -m server --host 0.0.0.0` with
  `GEO_AGENT_PASSWORT` set, and colleagues open `http://<PC name>:8500`.

### 3.3 The free hosts, compared

Checked on 2026-10-29. Free offers change often; where only secondary sources were found, it says so.

| Host | Free offer | Problem for GroundTwin |
|---|---|---|
| **Own PC + Cloudflare Tunnel** (§3.1) | Free, no account; your hardware | PC must be on; the address changes (chosen option) |
| Render Free | 512 MB RAM, 0.1 CPU; sleeps after 15 min without traffic (~1 min to wake up); 750 h per month; **no persistent disk** and it may restart at any time ([Render: deploy for free](https://render.com/docs/free); [pricing overview](https://temps.sh/blog/render-pricing-2026)) | Projects are lost on every sleep or restart; extraction very slow with 0.1 CPU |
| Hugging Face Spaces (Docker, CPU basic) | 2 vCPU, 16 GB RAM, 50 GB disk that does not persist; sleeps after 48 h without use ([Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [managing Spaces](https://huggingface.co/docs/huggingface_hub/main/guides/manage-spaces)) | Projects are lost on restart; persistent storage is now paid ([Spaces storage](https://huggingface.co/docs/hub/spaces-storage)); choosing the region is a paid feature ([storage regions](https://huggingface.co/docs/hub/storage-regions)), so free Spaces probably run outside the EU; a separate repository on HF |
| Koyeb | One web service with 512 MB RAM, 0.1 vCPU, 2 GB SSD, in Frankfurt or Washington; scales to zero after 1 h without traffic ([pricing FAQ](https://www.koyeb.com/docs/faq/pricing), [scale to zero](https://www.koyeb.com/docs/run-and-scale/scale-to-zero)) | Very slow; the disk does not persist |
| Oracle Cloud Always Free | Arm VMs with up to 4 OCPU and 24 GB according to the docs (2026 reports mention a cut to 2 OCPU / 12 GB) ([Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/resourceref.htm)) | Credit card, server administration, idle instances can be reclaimed; the Arm build of the dependencies is not tested |
| Railway | Trial credit; reports of a small monthly credit, not a permanent free tier ([overview](https://costbench.com/software/developer-tools/railway/free-plan/), secondary) | Not reliably free |
| Fly.io | No free tier for new accounts since October 2024 ([overview](https://costbench.com/software/developer-tools/flyio/free-plan), secondary) | — |

## 4. Render step by step (paid, for a permanent service)

1. **Bring the files to `main`.** `render.yaml` and `Dockerfile` have to be on `main` (merge the pull
   request): the blueprint deploys `main`.
2. **Create the blueprint.** On [render.com](https://render.com), sign in with GitHub → *New →
   Blueprint* → repository `martinpazmino/GroundTwin`. If Render does not see it, give it access on
   GitHub (*Configure GitHub App*). The *Deploy to Render* button in the README does the same.
3. **Check what it creates.** Render reads `render.yaml`:
   - web service `groundtwin` (Docker), region `frankfurt`, plan `starter`;
   - disk `groundtwin-daten` of 5 GB at `/data`;
   - health check at `/gesund`.
4. **Set the password.** Render asks for `GEO_AGENT_PASSWORT`, which is not stored in the repository.
   Choose a long password and share it only with the team.
5. **Apply and wait.** *Apply* starts the first build. The URL looks like
   `https://groundtwin-….onrender.com` (a custom domain can be added).
6. **Sign in.** When the URL is opened, the browser asks for user and password. The user can be
   anything, unless `GEO_AGENT_BENUTZER` is set.
7. **Update.** Every push to `main` builds and deploys again. The projects on `/data` are kept.

Costs **[to be verified on render.com/pricing]**:

| Plan | Resources | Price | For what |
|---|---|---|---|
| `starter` | 512 MB, 0.5 CPU | about $7/month | Without OCR |
| `standard` | 2 GB | about $25/month | OCR of scans or very large Gutachten |
| Disk | 5 GB | about $1.25/month ($0.25/GB) | Projects |
| `free` | 512 MB, 0.1 CPU | $0 | Only a demo: no disk (the projects are lost) and it sleeps without use (§3.3) |

If the platform reports a lack of memory (the service restarts during an extraction), move up a plan.

## 5. Other platforms: same repository, same Dockerfile

| Platform | How | Watch out |
|---|---|---|
| **Railway** | *New Project → Deploy from GitHub repo*. It detects the `Dockerfile`. Add a *Volume* at `/data` and the variable `GEO_AGENT_PASSWORT` | It sets `PORT` by itself |
| **Fly.io** | `fly launch` creates `fly.toml`; region `fra`. `fly volumes create` and mount it at `/data`. `fly secrets set GEO_AGENT_PASSWORT=…` | Deploying from GitHub goes through a GitHub Action |
| **Own server** (VPS, company server) | `docker run -d -p 8500:8500 -e GEO_AGENT_PASSWORT=… -v groundtwin-daten:/data groundtwin`, with Caddy or nginx in front for HTTPS | Full control; the data stays in-house (GDPR) |
| Google Cloud Run | Build from GitHub | No persistent disk by default and CPU only during requests **[to be verified]**: it does not fit the extraction thread |
| Hugging Face Spaces (Docker) | A separate Space with `app_port: 8500` | Its own repository on HF; not suitable for confidential Gutachten in a public Space |

## 6. Environment variables

| Variable | Default | For what |
|---|---|---|
| `PORT` | 8500 | Port. The platforms set it themselves |
| `GEO_AGENT_HOST` | `127.0.0.1` (in the container `0.0.0.0`) | Network interface. If it is not local and the password is missing, the server warns at start-up |
| `GEO_AGENT_PASSWORT` | — | Password (HTTP Basic) for everything except `/gesund`. **Without it the app is open** |
| `GEO_AGENT_BENUTZER` | — (any user) | Required user name |
| `GEO_AGENT_MAX_MB` | 200 | Maximum size of a request. Above it the server answers 413 |
| `GEO_AGENT_ARBEIT` | Temporary folder `geo_agent` (in the container `/data`) | Projects. Online **always** on a persistent disk |
| `GEO_AGENT_QUELLCODE` | `https://github.com/martinpazmino/GroundTwin` | *Quellcode* link (AGPL § 13). A fork with changes puts its own repository here |
| `CLOUDFLARED` | — | Path to `cloudflared` for `scripts/online.py`, if it is not on the `PATH` |

## 7. Memory and size (measured)

Image without OCR, in the session of 2026-10-29:

| Measure | Value |
|---|---|
| Image | 1.15 GB |
| Python dependencies | 686 MB: ifcopenshell 203, PyMuPDF 116, SciPy 109, onnxruntime 68 (brought in by PyMuPDF 2.0) |
| Memory at rest | 98 MB |
| Memory after the model of the 6 km Trasse | 161 MB |
| Memory after extracting the synthetic PDF | 290 MB |

With OCR, OpenCV and the RapidOCR models are added. OCR of large pages can need more than 1 GB
([X7](16_lessons_learned.md#x-working-environment)), so with scans a 2 GB plan is advisable.

## 8. Security, data and license

- **HTTPS** is provided by the platform (Render, Railway, Fly) or by Cloudflare (§3). On an own server,
  with Caddy or nginx in front.
- **One password for the whole team.** There are no users or per-project permissions: whoever has it
  sees all projects. For different clients, one instance per client. Later, Supabase with RLS
  ([architecture](ARCHITECTURE_BAUGRUNDMODELL.md)).
- **`/gesund`** answers without a password and only returns the version.
- **Confidential Gutachten:**
  - EU region (Frankfurt) or your own PC (§3);
  - a data processing agreement (AVV/DPA) with the provider;
  - the requirements in [14 §6](14_licensing.md#6-other-requirements-once-third-parties-come).
- **Backups:** the platform's disk does not replace your own copy. Export the important projects
  (IFC, JSON).
- **AGPL § 13:** the *Quellcode* link must stay visible and lead to the code of the deployed
  version. It is in the footer of the first page and in the ⋯ menu. Details in
  [THIRD_PARTY_LICENSES](../THIRD_PARTY_LICENSES.md) and [14](14_licensing.md).

## 9. Dependencies and versions

- `requirements-server.txt`: only what the app needs online.
- `requirements.txt`: adds Streamlit (Excel v1) and the tests.
- `requirements-ocr.txt`: the OCR.
- `constraints.txt`: the exact versions with which the image was built and tested (Python 3.13). The
  `Dockerfile` and the CI install with `-c constraints.txt`, so a deployment does not change versions
  by surprise.

To update the versions:

```bash
python3.13 -m venv /tmp/neu && /tmp/neu/bin/pip install -r requirements-server.txt -r requirements-ocr.txt
/tmp/neu/bin/pip freeze          # → constraints.txt (the OCR part in its own section)
pytest tests && (cd services/modeler && pytest tests)
docker build -t groundtwin .     # and check_app.mjs against the container (§11)
```

## 10. Automated tests (CI)

[`.github/workflows/pruefungen.yml`](../.github/workflows/pruefungen.yml) runs on every push and pull
request:

| Job | What it checks |
|---|---|
| Python | `pytest tests` (project, API, access, free online script) and the modeler with its norms |
| Oberfläche | `npm ci && npm run build`: the page compiles. `dist` still comes from the repository |
| Container | The image **with OCR** is built and started with a password: `/gesund`, 401 without the password, 200 with it, `import cv2, rapidocr_onnxruntime` |
| Ende zu Ende | Only on demand (*Run workflow*): `scripts/check_app.mjs` with Playwright; the screenshots are kept as an artifact |

## 11. What is tested

Tested in the session, with the image without OCR:
- the image builds and starts as user 1000;
- a root-owned volume is handed over to that user at start-up;
- 401 without the password, 200 with it;
- `/gesund` answers;
- the demo model comes out with 7 Einheiten and closed solids;
- **28/28 checks of `check_app.mjs` against the container, with a password**.

In GitHub's CI (first run on 2026-10-29, all green): the image **with OCR** builds, `ocr: true`,
OpenCV and RapidOCR import, 401/200.

The free option (§3) is tested with a simulated `cloudflared` (`tests/test_online.py`): address shown,
password enforced (401/200), Ctrl+C stops server and tunnel, a server without a password on the port
is refused. **Not tested here:** a real Cloudflare tunnel and `start_online.bat` on Windows.

**Not tested here** either (the session's network blocks deb.debian.org and render.com,
[X25](16_lessons_learned.md#x-working-environment)): the Render blueprint; it will show at the first
deployment.

Building locally:

```bash
docker build -t groundtwin .                          # with OCR
docker build -t groundtwin --build-arg OCR=0 .        # without OCR (smaller, no system packages)
docker run --rm -p 8500:8500 -e GEO_AGENT_PASSWORT=test -v "$(mktemp -d)":/data groundtwin
python scripts/testplan.py plans
GEO_AGENT_PASSWORT=test node scripts/check_app.mjs http://localhost:8500 plans screenshots
```

`check_app.mjs` logs in with the same password. It needs an **empty disk**: it creates projects and
changes the examples, so it must not be run against the real deployment.

Up: [Index](README.md)

Related: [21 Step app](21_app_schritte_normen.md) · [14 Licensing](14_licensing.md) · [11 Decisions](11_decisions.md) · [16 Lessons](16_lessons_learned.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)
