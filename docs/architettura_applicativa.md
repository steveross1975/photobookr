# Architettura Applicativa — PhotoBookr

**Versione:** 1.0  
**Data:** 2026-06-10

---

## 1. Visione d'insieme

PhotoBookr è strutturata come una **web application a singolo livello** (monolite modulare) con separazione netta tra layer di presentazione, business logic e accesso ai dati.

```
┌─────────────────────────────────────────────────────────┐
│                       Browser                           │
│              Jinja2 + Tailwind + Alpine.js              │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                    Flask (run.py)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ web.py   │  │templates │  │ projects │  │ photos │  │
│  │ (HTML)   │  │  (API)   │  │  (API)   │  │ (API)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│  ┌────────────────────────────────────────────────────┐ │
│  │                   export.py (API)                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │  database.py    │  │ pipeline.py│  │ exporter.py │  │
│  │  (SQLite ORM)   │  │  (OpenCV)  │  │ (ReportLab) │  │
│  └────────┬────────┘  └────────────┘  └─────────────┘  │
└───────────┼──────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────┐
│                    Filesystem locale                      │
│  data/fotolibro.db   data/customer_photos/   outputs/    │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Stack tecnologico

| Layer | Tecnologia | Versione | Ruolo |
|---|---|---|---|
| Web framework | Flask | 3.1.3 | Routing, template rendering |
| Template engine | Jinja2 | 3.1.6 | Rendering HTML server-side |
| Frontend reactivity | Alpine.js | 3.14.1 | Interattività client-side (CDN) |
| CSS utility | Tailwind CSS | latest | Stile UI (CDN) |
| Database | SQLite | — | Persistenza dati |
| DB driver | sqlite3 | stdlib | Accesso al DB (no ORM) |
| Image processing | OpenCV headless | 4.13.0 | Pipeline ottimizzazione AI |
| Image processing | Pillow | 12.1.1 | Supporto formati immagine |
| Numerics | NumPy | 2.4.2 | Operazioni array immagini |
| PDF generation | ReportLab | 4.4.10 | Export A3 PDF |
| Config | python-dotenv | 1.2.2 | Variabili d'ambiente |
| Runtime | Python | 3.13 | — |

---

## 3. Struttura del progetto

```
photobookr/
│
├── run.py                      # Entry point: crea l'app e avvia il server
│
├── app/
│   ├── __init__.py             # App factory (create_app)
│   │
│   ├── core/
│   │   ├── database.py         # Tutte le funzioni di accesso al DB
│   │   ├── pipeline.py         # Pipeline ottimizzazione immagini (OpenCV)
│   │   └── exporter.py         # Generazione PDF (ReportLab)
│   │
│   ├── routes/
│   │   ├── web.py              # Route HTML (pagine Jinja2)
│   │   ├── templates.py        # API /api/templates
│   │   ├── projects.py         # API /api/projects
│   │   ├── photos.py           # API /api/photos + enhance
│   │   └── export.py           # API /api/projects/<id>/export
│   │
│   ├── templates/              # Template HTML Jinja2
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── project.html
│   │   └── templates_page.html
│   │
│   └── static/
│       └── outputs/            # PDF generati (serviti da Flask)
│
├── data/
│   ├── fotolibro.db            # Database SQLite
│   ├── templates_master/       # File fisici dei template grafici
│   └── customer_photos/        # Foto caricate per progetto
│
├── docs/                       # Documentazione
├── requirements.txt
├── .env
└── .gitignore
```

---

## 4. Componenti principali

### 4.1 App Factory (`app/__init__.py`)

Segue il pattern **application factory** di Flask. `create_app()` è responsabile di:
- Caricare la configurazione da `.env`
- Inizializzare il database (`init_db()`)
- Registrare tutti i blueprint

Questo pattern rende l'app testabile in isolamento e prepara il terreno per configurazioni multiple (development / production).

### 4.2 Layer di accesso dati (`app/core/database.py`)

Accesso diretto a SQLite tramite `sqlite3` stdlib. Nessun ORM per mantenere la portabilità verso PostgreSQL.

Ogni funzione:
- Apre e chiude la propria connessione (`get_db_connection()`)
- Usa `conn.row_factory = sqlite3.Row` per accesso per nome colonna
- Gestisce transazioni esplicite con `try / rollback / finally`

**Funzioni per dominio:**

| Dominio | Funzioni |
|---|---|
| Template | `add_complete_template`, `register_complete_template`, `get_all_templates`, `get_template_by_id`, `get_template_components`, `update_template_complete`, `delete_template` |
| Progetti | `create_project`, `get_all_projects`, `get_project_by_id`, `update_project`, `set_project_output`, `delete_project` |
| Foto | `add_photo`, `get_photos_by_project`, `get_photo_by_id`, `update_photo`, `delete_photo` |

### 4.3 Pipeline AI (`app/core/pipeline.py`)

Elaborazione sincrona in 4 step sequenziali (OpenCV + NumPy):

```
Immagine originale
      │
      ▼
[1] White Balance (Gray World)
    Spazio colore LAB — neutralizza cast cromatici
      │
      ▼
[2] Auto Contrasto (CLAHE)
    Contrast Limited Adaptive Histogram Equalization
    sul canale L — migliora contrasto locale senza bruciare le luci
      │
      ▼
[3] Denoising
    fastNlMeansDenoisingColored — riduce il rumore preservando i bordi
      │
      ▼
[4] Sharpening (Unsharp Mask)
    Gaussian blur + weighted add — aumenta la nitidezza per la stampa
      │
      ▼
Immagine ottimizzata (file separato)
```

**Parametri chiave:**
- CLAHE: `clipLimit=2.0`, `tileGridSize=(8,8)`
- Denoising: `h=10`, `hColor=10`, `templateWindowSize=7`, `searchWindowSize=21`
- Sharpening: `sigma=3`, `alpha=1.5`, `beta=-0.5`

### 4.4 Exporter PDF (`app/core/exporter.py`)

Genera PDF A3 landscape (1190×842 pt) tramite ReportLab canvas API.

**Struttura pagine:**

```
PDF output
  ├── Pagina 1: Copertina
  │   └── Template cover (full-page, stretch)
  │
  ├── Pagine 2..N: Foto con position_data
  │   ├── Sfondo: template inner (full-page)
  │   └── Foto posizionate con coordinate {x,y,w,h} (valori 0-1 relativi)
  │
  └── Pagine N+1..M: Foto senza position_data (auto-grid)
      ├── Sfondo: template inner (full-page)
      └── Griglia 2×2, margine 10mm, gutter 4mm
```

### 4.5 Blueprint e routing

| Blueprint | Prefix | Tipo |
|---|---|---|
| `web` | `/` | HTML (Jinja2) |
| `templates` | `/api/templates` | JSON API |
| `projects` | `/api/projects` | JSON API |
| `photos` | `/api/photos`, `/api/projects/<id>/photos` | JSON API |
| `export` | `/api/projects/<id>/export` | JSON API |

### 4.6 Serving dei file media

`GET /media/<path>` in `web.py` serve i file locali con whitelist di sicurezza:
- Ammesso: `data/`
- Ammesso: `app/static/outputs/`
- Tutto il resto: 403 Forbidden

---

## 5. Flusso dati — Upload e ottimizzazione foto

```
Browser
  │  POST /api/projects/<id>/photos
  │  (multipart/form-data, n file)
  ▼
Flask route (photos.py)
  │  Validazione estensione
  │  Salvataggio: data/customer_photos/<pid>/<filename>
  │  INSERT INTO photos (original_path, sort_order)
  ▼
DB: record foto creato

Browser
  │  POST /api/projects/<id>/enhance
  ▼
Flask route (photos.py)
  │  Per ogni foto del progetto:
  │    pipeline.enhance_photo(original_abs, optimized_abs)
  │    UPDATE photos SET optimized_path = ...
  ▼
Filesystem: data/customer_photos/<pid>/optimized/<filename>
DB: optimized_path aggiornato
```

---

## 6. Flusso dati — Export PDF

```
Browser
  │  POST /api/projects/<id>/export
  ▼
Flask route (export.py)
  │  get_project_by_id(id)
  │  get_photos_by_project(id)
  │  get_template_components(template_id)
  ▼
exporter.export_project_pdf(project, photos, components, output_path, root)
  │  Canvas ReportLab A3 landscape
  │  Per ogni pagina:
  │    drawImage(template_inner)   ← sfondo
  │    drawImage(photo)            ← foto (positioned o grid)
  │  canvas.save()
  ▼
Filesystem: app/static/outputs/<pid>/NomeProgetto.pdf
DB: UPDATE projects SET status='completed', total_pages=N, output_folder=...
  ▼
Response JSON: { pdf_path, total_pages }
```

---

## 7. Considerazioni per lo scaling (Fase 2)

La v1.0 è progettata per facilitare la migrazione verso un'architettura multi-utente.

### Da SQLite a PostgreSQL

Il layer DB è completamente isolato in `database.py`. Non vengono usate feature SQLite-specifiche (escluso `AUTOINCREMENT` da rivedere → `SERIAL` in PostgreSQL). La migrazione richiede:
1. Sostituire `sqlite3` con `psycopg2` o `SQLAlchemy`
2. Adeguare i placeholder (`?` → `%s`)
3. Gestire il connection pool (attualmente ogni funzione apre/chiude la connessione)

### Da filesystem locale a object storage (S3)

Tutti i path sono relativi dalla root del progetto. I punti di accesso ai file sono limitati a:
- `database.py` (salva path nel DB)
- `pipeline.py` (`cv2.imread` / `cv2.imwrite`)
- `exporter.py` (`c.drawImage`)
- `web.py` → `/media/` route (`send_file`)
- Route upload in `photos.py` e `web.py`

Per migrare a S3: creare un modulo `app/core/storage.py` con interfaccia uniforme (`save_file`, `read_file`, `delete_file`, `get_url`) e sostituire i riferimenti diretti al filesystem.

### Autenticazione

Flask-Login o JWT. La struttura a blueprint facilita l'aggiunta di un decorator `@login_required` su tutti i blueprint in un unico punto (`create_app`).

### Pipeline asincrona

La pipeline AI è attualmente sincrona e blocca il server durante l'elaborazione. In produzione: sostituire con **Celery + Redis** (o RQ). Le route già ritornano un ID operazione — il pattern è già compatibile con un sistema task-based.

---

## 8. Sicurezza (v1.0)

| Rischio | Mitigazione |
|---|---|
| Path traversal nel media endpoint | Whitelist su `data/` e `app/static/outputs/` con `os.path.normpath` |
| Upload di file non immagine | Validazione estensione (whitelist) |
| SQL injection | Prepared statements con parametri `?` in tutti i `cursor.execute` |
| XSS | Jinja2 escaping automatico; Alpine.js usa binding sicuri |

**Non implementato in v1.0 (richiesto per Fase 2):**
- Autenticazione / autorizzazione
- Rate limiting
- CSRF protection (form HTML)
- Validazione MIME type effettivo dei file (oltre all'estensione)
