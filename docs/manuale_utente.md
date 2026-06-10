# Manuale Utente — PhotoBookr

## Cos'è PhotoBookr

PhotoBookr è un'applicazione desktop per la creazione di fotolibri in formato A3.  
Permette di caricare le foto di un servizio fotografico, migliorarle automaticamente con intelligenza artificiale e generare un PDF pronto per la stampa.

---

## Avvio dell'applicazione

1. Apri il terminale nella cartella del programma
2. Digita il comando:
   ```
   photobookr/bin/python run.py
   ```
3. Apri il browser e vai su: **http://localhost:5000**
4. L'applicazione è pronta all'uso

> Per chiudere l'applicazione, torna sul terminale e premi `Ctrl + C`.

---

## Flusso di lavoro consigliato

```
1. Crea un template  →  2. Crea un progetto  →  3. Carica le foto
                                                        ↓
                                          4. Migliora le foto (AI)
                                                        ↓
                                             5. Esporta il PDF
```

---

## Gestione Template

I template definiscono l'aspetto grafico del fotolibro: la copertina e il layout delle pagine interne.

### Creare un nuovo template

1. Clicca su **Template** nella barra in alto
2. Clicca su **Nuovo template**
3. Compila i campi:
   - **Nome**: nome descrittivo (es. "Matrimonio Elegante")
   - **Categoria**: tipo di servizio (es. matrimonio, viaggio, classe)
   - **Copertina**: carica l'immagine A3 per la prima pagina
   - **Pagina interna**: carica l'immagine A3 da usare come sfondo
4. Clicca **Salva template**

> I file immagine del template devono essere in formato A3 (420×297 mm).  
> Formati supportati: JPG, PNG, TIFF.

### Eliminare un template

Nella pagina Template, clicca sull'icona del cestino sulla card del template.  
Verrà chiesta conferma prima dell'eliminazione.

---

## Gestione Progetti

Ogni progetto corrisponde a un singolo fotolibro da consegnare a un cliente.

### Creare un nuovo progetto

1. Dalla **Dashboard** (pagina iniziale), clicca su **Nuovo progetto**
2. Compila i campi:
   - **Nome fotolibro** *(obbligatorio)*: es. "Matrimonio Bianchi 2025"
   - **Cliente** *(opzionale)*: es. "Mario e Laura Bianchi"
   - **Template** *(opzionale)*: scegli il template grafico da applicare
3. Clicca **Crea progetto**

Verrai indirizzato automaticamente alla pagina del progetto.

### Aprire un progetto esistente

Dalla Dashboard, clicca sulla card del progetto che vuoi aprire.

---

## Caricamento delle foto

Nella pagina del progetto trovi la zona di caricamento.

### Trascinamento (metodo consigliato)

1. Seleziona le foto dal tuo computer
2. Trascinale direttamente sull'area tratteggiata **"Trascina le foto qui"**
3. Attendi il completamento del caricamento

### Selezione manuale

1. Clicca su **Seleziona file** nell'area di caricamento
2. Scegli una o più foto dalla finestra di selezione
3. Clicca **Apri**

> **Formati supportati:** JPG, JPEG, PNG, TIFF  
> È possibile caricare più foto contemporaneamente.

Le foto caricate appaiono nella griglia sottostante con una piccola anteprima.

---

## Miglioramento automatico con AI

PhotoBookr applica una pipeline di ottimizzazione automatica per migliorare la qualità delle foto prima della stampa.

### Cosa fa la pipeline AI

| Passaggio | Effetto |
|---|---|
| Bilanciamento del bianco | Rimuove i cast di colore (tinte giallastre, bluastre, ecc.) |
| Contrasto adattivo | Migliora i dettagli in ombre e luci senza bruciare |
| Riduzione del rumore | Elimina il grano fotografico |
| Nitidezza | Aumenta la definizione per la stampa |

### Come avviare il miglioramento

1. Nella pagina del progetto, clicca **✨ Migliora tutte le foto**
2. Attendi il completamento (il pulsante mostra uno spinner durante l'elaborazione)
3. Le foto ottimizzate mostrano il badge verde **✓ AI**

> L'originale non viene mai sovrascritto. Le versioni migliorate sono copie separate.

---

## Esportazione PDF

### Generare il PDF

1. Nella pagina del progetto, clicca **📄 Esporta PDF**
2. Attendi la generazione (può richiedere qualche secondo)
3. Quando pronto, appare il pulsante **⬇️ Scarica PDF**
4. Clicca per scaricare il file

### Struttura del PDF generato

- **Prima pagina**: copertina del template (se presente)
- **Pagine successive**: foto disposte in una griglia 2×2 su sfondo del template interno

Il progetto viene marcato automaticamente come **Completato** dopo l'export.

---

## Stati di un progetto

| Stato | Significato |
|---|---|
| **Bozza** | Progetto creato, foto non ancora esportate |
| **In lavorazione** | Elaborazione in corso |
| **Completato** | PDF generato con successo |

---

## Domande frequenti

**Posso aggiungere altre foto dopo l'esportazione?**  
Sì. Puoi caricare nuove foto e riesportare il PDF in qualsiasi momento.

**Posso usare più template per lo stesso progetto?**  
No, ogni progetto usa un solo template. Per cambiarlo è necessario modificarlo dalle impostazioni del progetto.

**Le foto originali vengono modificate?**  
No. Il miglioramento AI crea sempre copie separate. Gli originali rimangono intatti.

**Il PDF è pronto per la stampa professionale?**  
Il PDF è generato in formato A3 landscape. Verifica con la tua tipografia i requisiti specifici (DPI, profilo colore ICC).

**Posso eliminare una foto dal progetto?**  
Sì. Passa il mouse sopra la foto nella griglia e clicca sulla **X** rossa che appare nell'angolo.
