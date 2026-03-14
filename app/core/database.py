import os
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

    # 1. Tabella Template (Master A3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_path TEXT NOT NULL,       -- Path del file A3 (copertina o interno)
            type TEXT CHECK(type IN ('cover', 'inner')) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabella Progetti (Istanze dei fotolibri)
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

    # 3. Tabella Foto (Singoli scatti ottimizzati e posizionati)
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

def add_template(name, file_path, template_type):
    """Registra un nuovo template A3 nel database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO templates (name, file_path, type, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, file_path, template_type))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Errore durante l'inserimento del template: {e}")
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

# --- END TEMPLATE FUNCTIONS ---

if __name__ == "__main__":
    init_db()
    init_db()
