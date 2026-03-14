import os
import shutil
import sqlite3

#from datetime import datetime

# Percorso del database relativo alla root del progetto
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/fotolibro.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permette di accedere alle colonne per nome
    return conn

def init_db():
    """Inizializza le tabelle del database all'avvio"""
    # Assicurati che la cartella data esista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabella Template (L'identità del tema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,            -- Es: "Viaggio in Giappone"
            category TEXT NOT NULL,        -- Es: "viaggio", "classe"
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabella Componenti (I file fisici A3 collegati al template)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS template_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,       -- Path del file A3
            component_type TEXT CHECK(component_type IN ('cover', 'inner')) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE CASCADE
        )
    ''')

    # 3. Tabella Progetti (Istanze dei fotolibri)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            customer_name TEXT,
            template_id INTEGER,
            total_pages INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',    -- draft, processing, completed
            output_folder TEXT,             -- Cartella finale dei JPG/PDF
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')

    # 4. Tabella Foto (Singoli scatti ottimizzati e posizionati)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            original_path TEXT NOT NULL,
            optimized_path TEXT,            -- Path della versione AI-improved
            page_number INTEGER,            -- In quale pagina A3 è finita
            position_data TEXT,             -- JSON con coordinate {x, y, w, h}
            sort_order TEXT,                -- Nome file per ordinamento alfabetico
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database inizializzato correttamente.")

# --- BEGIN TEMPLATE FUNCTIONS ---

def add_complete_template(name, category, cover_path, inner_path):
    """Inserisce un template e i suoi due componenti in un'unica transazione"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Inserisco il Template "Padre"
        cursor.execute('''
            INSERT INTO templates (name, category, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (name, category.lower()))
        
        template_id = cursor.lastrowid
        
        # Inserisco i Componenti "Figli"
        components = [
            (template_id, cover_path, 'cover'),
            (template_id, inner_path, 'inner')
        ]
        cursor.executemany('''
            INSERT INTO template_components (template_id, file_path, component_type, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', components)
        
        conn.commit()
        return template_id
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore: {e}")
        return None
    finally:
        conn.close()


def get_all_templates():
    """Ritorna la lista di tutti i template disponibili"""
    conn = get_db_connection()
    templates = conn.execute('SELECT * FROM templates ORDER BY created_at DESC').fetchall()
    conn.close()
    return templates

def delete_template(template_id):
    """Rimuove un template dal database (il file fisico andrà rimosso a parte)"""
    conn = get_db_connection()
    conn.execute('DELETE FROM templates WHERE id = ?', (template_id,))
    conn.commit()
    conn.close()

def get_template_by_id(template_id):
    """Recupera i dettagli di un singolo template tramite il suo ID"""
    conn = get_db_connection()
    # Usiamo .fetchone() perché l'ID è univoco
    template = conn.execute('SELECT * FROM templates WHERE id = ?', (template_id,)).fetchone()
    conn.close()
    return template

def update_template_complete(template_id, name, category, cover_path=None, inner_path=None):
    """
    Aggiorna l'anagrafica del template e, se forniti, i percorsi dei file componenti.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Aggiorna il record Padre (Anagrafica)
        cursor.execute('''
            UPDATE templates 
            SET name = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, category.lower(), template_id))

        # 2. Aggiorna i Componenti (se i percorsi sono forniti)
        if cover_path:
            cursor.execute('''
                UPDATE template_components 
                SET file_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE template_id = ? AND component_type = 'cover'
            ''', (cover_path, template_id))
            
        if inner_path:
            cursor.execute('''
                UPDATE template_components 
                SET file_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE template_id = ? AND component_type = 'inner'
            ''', (inner_path, template_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore aggiornamento completo template: {e}")
        return False
    finally:
        conn.close()

def register_complete_template(name, category, source_cover_path, source_inner_path):
    """
    Logica completa: 
    1. Registra l'identità del Template (Padre) nel DB.
    2. Copia e rinomina i due file fisici (Cover e Inner) nella cartella master.
    3. Registra i due componenti (Figli) collegandoli al Template.
    """
    dest_dir = os.path.join(os.path.dirname(__file__), '../../data/templates_master')
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. Creiamo il record del Template Padre
    template_id = add_template_record(name, category) # Funzione di supporto da aggiungere
    if not template_id: 
        return None

    files_to_process = [
        (source_cover_path, 'cover'),
        (source_inner_path, 'inner')
    ]

    try:
        conn = get_db_connection()
        for source_path, comp_type in files_to_process:
            # Generiamo un nome file pulito: es. "viaggio_giappone_cover.jpg"
            ext = os.path.splitext(source_path)[1]
            clean_name = name.replace(' ', '_').lower()
            filename = f"{clean_name}_{comp_type}{ext}"
            dest_path = os.path.join(dest_dir, filename)
            
            # Copia fisica
            shutil.copy2(source_path, dest_path)
            
            # Registrazione componente nel DB
            relative_path = os.path.join('data/templates_master', filename)
            conn.execute('''
                INSERT INTO template_components (template_id, file_path, component_type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (template_id, relative_path, comp_type))
            
        conn.commit()
        return template_id
    except Exception as e:
        print(f"Errore durante la registrazione dei file template: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def add_template_record(name, category):
    """Semplice inserimento del record padre"""
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO templates (name, category, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (name, category.lower()))
        template_id = cursor.lastrowid
        conn.commit()
        return template_id
    except sqlite3.Error as e:
        print(f"Errore inserimento record padre: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()