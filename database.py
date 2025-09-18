import sqlite3
import uuid
import json
from datetime import datetime
import os

DATABASE_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id TEXT PRIMARY KEY,
            song_name TEXT NOT NULL,
            artist TEXT,
            version TEXT,
            notes TEXT,
            uploaded_by TEXT NOT NULL,
            uploaded_at TIMESTAMP NOT NULL,
            midi_filename TEXT,
            source_filename TEXT,
            lyric_filename TEXT,
            track_names TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_song(song_name, artist, version, notes, uploaded_by, midi_filename, source_filename, lyric_filename, track_names):
    conn = get_db_connection()
    song_id = str(uuid.uuid4())
    track_names_json = json.dumps(track_names) if track_names else None

    conn.execute('''
        INSERT INTO songs (id, song_name, artist, version, notes, uploaded_by, uploaded_at,
                          midi_filename, source_filename, lyric_filename, track_names)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (song_id, song_name, artist, version, notes, uploaded_by, datetime.now(),
          midi_filename, source_filename, lyric_filename, track_names_json))

    conn.commit()
    conn.close()
    return song_id

def get_all_songs():
    conn = get_db_connection()
    songs = conn.execute('''
        SELECT * FROM songs ORDER BY uploaded_at ASC
    ''').fetchall()
    conn.close()

    # Add face_id based on upload order
    songs_list = []
    for i, song in enumerate(songs, 1):
        song_dict = dict(song)
        song_dict['face_id'] = i
        if song_dict['track_names']:
            song_dict['track_names'] = json.loads(song_dict['track_names'])
        songs_list.append(song_dict)

    return songs_list

def get_song_by_id(song_id):
    conn = get_db_connection()
    song = conn.execute('SELECT * FROM songs WHERE id = ?', (song_id,)).fetchone()
    conn.close()

    if song:
        song_dict = dict(song)
        if song_dict['track_names']:
            song_dict['track_names'] = json.loads(song_dict['track_names'])
        return song_dict
    return None

def update_song(song_id, song_name, artist, version, notes, uploaded_by, midi_filename=None, source_filename=None, lyric_filename=None, track_names=None):
    conn = get_db_connection()

    # Get current song data
    current_song = conn.execute('SELECT * FROM songs WHERE id = ?', (song_id,)).fetchone()
    if not current_song:
        conn.close()
        return False

    # Use existing filenames if new ones not provided
    if midi_filename is None:
        midi_filename = current_song['midi_filename']
    if source_filename is None:
        source_filename = current_song['source_filename']
    if lyric_filename is None:
        lyric_filename = current_song['lyric_filename']
    if track_names is None:
        track_names = json.loads(current_song['track_names']) if current_song['track_names'] else None

    track_names_json = json.dumps(track_names) if track_names else None

    conn.execute('''
        UPDATE songs SET song_name = ?, artist = ?, version = ?, notes = ?, uploaded_by = ?,
                        midi_filename = ?, source_filename = ?, lyric_filename = ?, track_names = ?
        WHERE id = ?
    ''', (song_name, artist, version, notes, uploaded_by, midi_filename, source_filename, lyric_filename, track_names_json, song_id))

    conn.commit()
    conn.close()
    return True

def delete_song(song_id):
    conn = get_db_connection()
    song = conn.execute('SELECT * FROM songs WHERE id = ?', (song_id,)).fetchone()

    if song:
        # Delete associated files
        for filename in [song['midi_filename'], song['source_filename'], song['lyric_filename']]:
            if filename:
                file_path = os.path.join('static', 'uploads', filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

        # Delete from database
        conn.execute('DELETE FROM songs WHERE id = ?', (song_id,))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False