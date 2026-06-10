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
    dest_dir = os.path.join(os.path.dirname(__file__), '../../data/templates_master')
    os.makedirs(dest_dir, exist_ok=True)

    files_to_process = [
        (source_cover_path, 'cover'),
        (source_inner_path, 'inner')
    ]

    copied_files = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO templates (name, category, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (name, category.lower()))
        template_id = cursor.lastrowid

        for source_path, comp_type in files_to_process:
            ext = os.path.splitext(source_path)[1]
            clean_name = name.replace(' ', '_').lower()
            filename = f"{clean_name}_{comp_type}{ext}"
            dest_path = os.path.join(dest_dir, filename)

            shutil.copy2(source_path, dest_path)
            copied_files.append(dest_path)

            relative_path = os.path.join('data/templates_master', filename)
            cursor.execute('''
                INSERT INTO template_components (template_id, file_path, component_type, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (template_id, relative_path, comp_type))

        conn.commit()
        return template_id
    except Exception as e:
        conn.rollback()
        for path in copied_files:
            if os.path.exists(path):
                os.remove(path)
        print(f"Errore registrazione template: {e}")
        return None
    finally:
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

# --- BEGIN PROJECT FUNCTIONS ---

def get_all_projects():
    conn = get_db_connection()
    projects = conn.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
    conn.close()
    return projects

def get_project_by_id(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    return project

def create_project(project_name, customer_name=None, template_id=None):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO projects (project_name, customer_name, template_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (project_name, customer_name, template_id))
        project_id = cursor.lastrowid
        conn.commit()
        return project_id
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore creazione progetto: {e}")
        return None
    finally:
        conn.close()

def update_project(project_id, project_name, customer_name=None, template_id=None, status=None):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE projects
            SET project_name = ?, customer_name = ?, template_id = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (project_name, customer_name, template_id, status, project_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore aggiornamento progetto: {e}")
        return False
    finally:
        conn.close()

def delete_project(project_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()

# --- BEGIN PHOTO FUNCTIONS ---

def get_photos_by_project(project_id):
    conn = get_db_connection()
    photos = conn.execute(
        'SELECT * FROM photos WHERE project_id = ? ORDER BY sort_order',
        (project_id,)
    ).fetchall()
    conn.close()
    return photos

def get_photo_by_id(photo_id):
    conn = get_db_connection()
    photo = conn.execute('SELECT * FROM photos WHERE id = ?', (photo_id,)).fetchone()
    conn.close()
    return photo

def add_photo(project_id, original_path, sort_order):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO photos (project_id, original_path, sort_order, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (project_id, original_path, sort_order))
        photo_id = cursor.lastrowid
        conn.commit()
        return photo_id
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore inserimento foto: {e}")
        return None
    finally:
        conn.close()

def update_photo(photo_id, page_number=None, position_data=None, optimized_path=None):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE photos
            SET page_number = ?, position_data = ?, optimized_path = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (page_number, position_data, optimized_path, photo_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Errore aggiornamento foto: {e}")
        return False
    finally:
        conn.close()

def delete_photo(photo_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM photos WHERE id = ?', (photo_id,))
    conn.commit()
    conn.close()

# if __name__ == "__main__":
#    init_db()


# Test rapido per verificare che tutto funzioni correttamente
if __name__ == "__main__":
    # 1. Reset/Inizializzazione DB
    print("--- FASE 1: Inizializzazione ---")
    init_db()
    
    # 2. Test Registrazione Template Completo
    print("\n--- FASE 2: Test Inserimento Template ---")
    # Assicurati che i file test_cover.jpg e test_inner.jpg esistano nella root
    if os.path.exists("test_cover.jpg") and os.path.exists("test_inner.jpg"):
        new_id = register_complete_template(
            name="Viaggio in Giappone", 
            category="viaggio", 
            source_cover_path="test_cover.jpg", 
            source_inner_path="test_inner.jpg"
        )
        if new_id:
            print(f"Successo! Creato template con ID: {new_id}")
        else:
            print("Errore durante la registrazione.")
    else:
        print("Attenzione: Crea i file test_cover.jpg e test_inner.jpg per testare la copia fisica.")

    # 3. Test Lettura
    print("\n--- FASE 3: Verifica Dati nel DB ---")
    templates = get_all_templates()
    for t in templates:
        print(f"Template trovato: {t['name']} (Categoria: {t['category']}) - Creato il: {t['created_at']}")
