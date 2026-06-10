# Specifica Tecnico-Funzionale — PhotoBookr

**Versione:** 1.0  
**Data:** 2026-06-10  
**Stato:** Draft

---

## 1. Scopo del documento

Questo documento descrive i requisiti funzionali e le specifiche tecniche di PhotoBookr, un'applicazione per la creazione di fotolibri A3 con pipeline di ottimizzazione AI ed esportazione PDF.

---

## 2. Panoramica del sistema

PhotoBookr è un'applicazione web single-user che gira localmente sulla macchina dell'utente (fotografo professionista). Permette di:

- Gestire template grafici per i fotolibri (copertina + pagina interna A3)
- Creare progetti fotolibro associati a un cliente
- Caricare e organizzare le foto di un servizio
- Ottimizzare automaticamente le foto per la stampa via pipeline AI
- Generare un PDF A3 landscape pronto per la stampa professionale

---

## 3. Attori

| Attore | Descrizione |
|---|---|
| **Fotografo** | Unico utente dell'applicazione. Crea e gestisce tutti i progetti. |

*(Fase 2: multi-utente con autenticazione — fuori scope dalla v1.0)*

---

## 4. Casi d'uso

### UC-01 — Gestione Template

| Campo | Dettaglio |
|---|---|
| **Attore** | Fotografo |
| **Precondizione** | — |
| **Flusso principale** | 1. Fotografo apre pagina Template → 2. Clicca "Nuovo template" → 3. Inserisce nome, categoria, carica copertina e pagina interna → 4. Sistema copia i file in `data/templates_master/` e registra nel DB → 5. Template disponibile per i progetti |
| **Flusso alternativo** | Se manca uno dei campi obbligatori il form non viene sottomesso |
| **Postcondizione** | Record in `templates` + 2 record in `template_components` |

### UC-02 — Creazione Progetto

| Campo | Dettaglio |
|---|---|
| **Attore** | Fotografo |
| **Precondizione** | — |
| **Flusso principale** | 1. Dashboard → "Nuovo progetto" → 2. Inserisce nome, cliente (opzionale), template (opzionale) → 3. Sistema crea record in `projects` con `status=draft` → 4. Redirect alla pagina progetto |
| **Postcondizione** | Record in `projects`, status = `draft` |

### UC-03 — Caricamento Foto

| Campo | Dettaglio |
|---|---|
| **Attore** | Fotografo |
| **Precondizione** | Progetto esistente |
| **Flusso principale** | 1. Fotografo trascina file o usa il selettore → 2. Sistema valida estensione → 3. Salva in `data/customer_photos/<project_id>/` → 4. Crea record in `photos` con `sort_order = nome_file` → 5. Anteprima aggiornata nella griglia |
| **Flusso alternativo** | Formato non supportato → errore 415, file non salvato |
| **Postcondizione** | File fisico + record in `photos` |

### UC-04 — Ottimizzazione AI

| Campo | Dettaglio |
|---|---|
| **Attore** | Fotografo |
| **Precondizione** | Almeno una foto caricata |
| **Flusso principale** | 1. Click "Migliora tutte le foto" → 2. Sistema esegue pipeline su ogni foto → 3. Salva in `data/customer_photos/<project_id>/optimized/` → 4. Aggiorna `optimized_path` nel DB → 5. Badge "✓ AI" visibile sulle foto |
| **Flusso alternativo** | File originale mancante su disco → errore registrato, le altre foto continuano |
| **Postcondizione** | File ottimizzati su disco, `optimized_path` popolato |

### UC-05 — Esportazione PDF

| Campo | Dettaglio |
|---|---|
| **Attore** | Fotografo |
| **Precondizione** | Almeno una foto caricata |
| **Flusso principale** | 1. Click "Esporta PDF" → 2. Sistema genera PDF A3 landscape → 3. Salva in `app/static/outputs/<project_id>/` → 4. Aggiorna `output_folder`, `total_pages`, `status=completed` → 5. Link download disponibile |
| **Postcondizione** | PDF su disco, progetto `completed` |

---

## 5. Regole di business

### Validazione file
- Estensioni ammesse per le foto: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`
- Estensioni ammesse per i template: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`
- Upload multiplo supportato in un'unica richiesta

### Stato progetto
- Transizioni ammesse: `draft` → `processing` → `completed`
- Il sistema imposta automaticamente `completed` dopo l'export
- L'utente può impostare `status` via API PUT

### Ordinamento foto
- Le foto sono ordinate per `sort_order` (nome file in ordine alfabetico)
- Convenzione consigliata: `001_nome.jpg`, `002_nome.jpg`, ecc.

### File originali
- Non vengono mai sovrascritti
- La versione ottimizzata viene salvata in una sottocartella `/optimized/`
- In caso di ri-ottimizzazione, il file ottimizzato viene sovrascritto

### Template
- Ogni template ha esattamente 2 componenti: `cover` e `inner`
- L'eliminazione di un template rimuove i record DB ma **non** i file fisici

### PDF — struttura pagine
- Pagina 1: sempre la copertina del template (se presente), altrimenti pagina bianca
- Pagine successive: se le foto hanno `position_data` → layout manuale raggruppato per `page_number`
- Foto senza `position_data` → auto-grid 2×2 (max 4 foto per pagina)
- Viene usata la versione ottimizzata se disponibile, altrimenti l'originale

---

## 6. API REST

### Template

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/api/templates` | Lista tutti i template |
| GET | `/api/templates/<id>` | Dettaglio template |
| POST | `/api/templates` | Crea template (multipart: `name`, `category`, `cover`, `inner`) |
| PUT | `/api/templates/<id>` | Aggiorna template |
| DELETE | `/api/templates/<id>` | Elimina template |

### Progetti

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/api/projects` | Lista progetti |
| GET | `/api/projects/<id>` | Dettaglio progetto |
| POST | `/api/projects` | Crea progetto (JSON: `project_name`, `customer_name?`, `template_id?`) |
| PUT | `/api/projects/<id>` | Aggiorna progetto (partial update) |
| DELETE | `/api/projects/<id>` | Elimina progetto |

### Foto

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/api/projects/<id>/photos` | Lista foto del progetto |
| POST | `/api/projects/<id>/photos` | Upload foto (multipart: `photos[]`) |
| GET | `/api/photos/<id>` | Dettaglio foto |
| PUT | `/api/photos/<id>` | Aggiorna `page_number`, `position_data`, `optimized_path` |
| DELETE | `/api/photos/<id>` | Elimina foto (DB + file fisico) |

### Pipeline e Export

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/api/photos/<id>/enhance` | Ottimizza singola foto |
| POST | `/api/projects/<id>/enhance` | Ottimizza tutte le foto del progetto |
| POST | `/api/projects/<id>/export` | Genera PDF del progetto |

### Media

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/media/<path>` | Serve file da `data/` o `app/static/outputs/` |

---

## 7. Modello dati

### Tabella `templates`

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT NOT NULL | Nome del template |
| `category` | TEXT NOT NULL | Categoria (lowercase) |
| `created_at` | DATETIME | Auto |
| `updated_at` | DATETIME | Aggiornato ad ogni modifica |

### Tabella `template_components`

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `template_id` | INTEGER FK | → `templates.id` ON DELETE CASCADE |
| `file_path` | TEXT NOT NULL | Path relativo dalla root del progetto |
| `component_type` | TEXT | `cover` oppure `inner` |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### Tabella `projects`

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `project_name` | TEXT NOT NULL | |
| `customer_name` | TEXT | Opzionale |
| `template_id` | INTEGER FK | → `templates.id` |
| `total_pages` | INTEGER | Default 0, aggiornato dopo export |
| `status` | TEXT | `draft` / `processing` / `completed` |
| `output_folder` | TEXT | Path relativo della cartella output |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

### Tabella `photos`

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `project_id` | INTEGER FK | → `projects.id` |
| `original_path` | TEXT NOT NULL | Path relativo del file originale |
| `optimized_path` | TEXT | Path relativo versione AI-ottimizzata |
| `page_number` | INTEGER | Numero pagina A3 (layout manuale) |
| `position_data` | TEXT | JSON `{"x": 0.1, "y": 0.2, "w": 0.4, "h": 0.3}` (valori 0-1) |
| `sort_order` | TEXT | Nome file per ordinamento alfabetico |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

---

## 8. Struttura delle cartelle di lavoro

```
data/
  fotolibro.db                        # Database SQLite
  templates_master/                   # File fisici dei template
    nome_template_cover.jpg
    nome_template_inner.jpg
  customer_photos/
    <project_id>/                     # Foto originali per progetto
      foto_001.jpg
      optimized/                      # Versioni AI-ottimizzate
        foto_001.jpg

app/static/outputs/
  <project_id>/                       # PDF generati
    NomeProgetto.pdf
```

---

## 9. Vincoli e limitazioni v1.0

- Single-user: nessuna autenticazione
- Database: SQLite (non adatto a deployment multi-utente)
- Storage: filesystem locale (non compatibile con cloud senza refactor)
- Concorrenza: nessuna gestione di richieste parallele
- La pipeline AI è sincrona: richieste lunghe bloccano il server
- Il layout editor (posizionamento manuale foto) non è implementato nella v1.0
