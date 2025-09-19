from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import uuid
import zipfile
import io
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from database import init_database, create_song, get_all_songs, get_song_by_id, update_song, delete_song
from midi_parser import parse_midi_tracks

app = Flask(__name__)
app.secret_key = 'sleepy-story-midi-sharing-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename, file_type):
    if file_type == 'midi':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['mid', 'midi']
    elif file_type == 'source':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'musz'
    elif file_type == 'lyric':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'lrc'
    return False


def save_uploaded_file(file, file_type):
    if file and file.filename and allowed_file(file.filename, file_type):
        # Generate hash-based sanitized filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        hash_input = f"{file.filename}_{uuid.uuid4().hex}".encode('utf-8')
        file_hash = hashlib.md5(hash_input).hexdigest()[:12]
        unique_filename = f"{file_hash}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return unique_filename, filepath
    return None, None

@app.route('/')
def index():
    songs = get_all_songs()
    return render_template('index.html', songs=songs)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            # Get form data
            song_name = request.form.get('song_name', '').strip()
            artist = request.form.get('artist', '').strip() or None
            version = request.form.get('version', '').strip() or None
            notes = request.form.get('notes', '').strip() or None
            uploaded_by = request.form.get('uploaded_by', '').strip()

            # Validation
            if not song_name:
                flash('歌曲名不能为空')
                return render_template('upload.html')

            if not uploaded_by or uploaded_by not in ['D', 'M', 'J']:
                flash('请选择有效的上传者角色')
                return render_template('upload.html')

            # Handle file uploads
            midi_file = request.files.get('midi_file')
            source_file = request.files.get('source_file')
            lyric_file = request.files.get('lyric_file')

            if not midi_file or not midi_file.filename:
                flash('请选择MIDI文件')
                return render_template('upload.html')

            # Save MIDI file and parse tracks
            midi_filename, midi_filepath = save_uploaded_file(midi_file, 'midi')
            if not midi_filename:
                flash('MIDI文件格式不正确')
                return render_template('upload.html')

            track_names = parse_midi_tracks(midi_filepath)

            # Save other files
            source_filename, _ = save_uploaded_file(source_file, 'source')
            lyric_filename, _ = save_uploaded_file(lyric_file, 'lyric')

            # Create song record
            song_id = create_song(
                song_name=song_name,
                artist=artist,
                version=version,
                notes=notes,
                uploaded_by=uploaded_by,
                midi_filename=midi_filename,
                source_filename=source_filename,
                lyric_filename=lyric_filename,
                track_names=track_names
            )

            flash(f'歌曲 "{song_name}" 上传成功')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'上传失败: {str(e)}')
            return render_template('upload.html')

    return render_template('upload.html')

@app.route('/edit/<song_id>', methods=['GET', 'POST'])
def edit(song_id):
    song = get_song_by_id(song_id)
    if not song:
        flash('歌曲不存在')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Get form data
            song_name = request.form.get('song_name', '').strip()
            artist = request.form.get('artist', '').strip() or None
            version = request.form.get('version', '').strip() or None
            notes = request.form.get('notes', '').strip() or None
            uploaded_by = request.form.get('uploaded_by', '').strip()

            # Validation
            if not song_name:
                flash('歌曲名不能为空')
                return render_template('upload.html', song=song)

            if not uploaded_by or uploaded_by not in ['D', 'M', 'J']:
                flash('请选择有效的上传者角色')
                return render_template('upload.html', song=song)

            # Handle file uploads (optional for edit)
            midi_file = request.files.get('midi_file')
            source_file = request.files.get('source_file')
            lyric_file = request.files.get('lyric_file')

            midi_filename = None
            track_names = None

            # Update MIDI file if provided
            if midi_file and midi_file.filename:
                # Delete old MIDI file
                if song['midi_filename']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], song['midi_filename'])
                    if os.path.exists(old_path):
                        os.remove(old_path)

                midi_filename, midi_filepath = save_uploaded_file(midi_file, 'midi')
                if not midi_filename:
                    flash('MIDI文件格式不正确')
                    return render_template('upload.html', song=song)
                track_names = parse_midi_tracks(midi_filepath)

            # Update source file if provided
            source_filename = None
            if source_file and source_file.filename:
                if song['source_filename']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], song['source_filename'])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                source_filename, _ = save_uploaded_file(source_file, 'source')

            # Update lyric file if provided
            lyric_filename = None
            if lyric_file and lyric_file.filename:
                if song['lyric_filename']:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], song['lyric_filename'])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                lyric_filename, _ = save_uploaded_file(lyric_file, 'lyric')

            # Update song record
            success = update_song(
                song_id=song_id,
                song_name=song_name,
                artist=artist,
                version=version,
                notes=notes,
                uploaded_by=uploaded_by,
                midi_filename=midi_filename,
                source_filename=source_filename,
                lyric_filename=lyric_filename,
                track_names=track_names
            )

            if success:
                flash(f'歌曲 "{song_name}" 更新成功')
                return redirect(url_for('index'))
            else:
                flash('更新失败')

        except Exception as e:
            flash(f'更新失败: {str(e)}')

    return render_template('upload.html', song=song)


@app.route('/delete/<song_id>')
def delete(song_id):
    song = get_song_by_id(song_id)
    if song:
        success = delete_song(song_id)
        if success:
            flash(f'歌曲 "{song["song_name"]}" 删除成功')
        else:
            flash('删除失败')
    else:
        flash('歌曲不存在')

    return redirect(url_for('index'))

@app.route('/download/<song_id>/<file_type>')
def download_file(song_id, file_type):
    song = get_song_by_id(song_id)
    if not song:
        flash('歌曲不存在')
        return redirect(url_for('index'))

    filename = None
    if file_type == 'midi':
        filename = song['midi_filename']
    elif file_type == 'source':
        filename = song['source_filename']
    elif file_type == 'lyric':
        filename = song['lyric_filename']

    if not filename:
        flash('文件不存在')
        return redirect(url_for('index'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('文件不存在')
        return redirect(url_for('index'))

    # Generate download filename based on specs
    songs = get_all_songs()
    face_id = next((s['face_id'] for s in songs if s['id'] == song_id), 1)

    # Include artist if available
    artist_part = f" - {song['artist']}" if song['artist'] else ""
    version_part = f" - v{song['version']}" if song['version'] else ""

    if file_type == 'midi':
        download_name = f"{face_id:03d}{song['uploaded_by']} - {song['song_name']}{artist_part}{version_part}.mid"
    elif file_type == 'source':
        download_name = f"{face_id:03d}{song['uploaded_by']} - {song['song_name']}{artist_part}{version_part}.musz"
    elif file_type == 'lyric':
        download_name = f"{face_id:03d}{song['uploaded_by']} - {song['song_name']}{artist_part}{version_part}.lrc"

    return send_file(filepath, as_attachment=True, download_name=download_name)

@app.route('/download_all')
def download_all():
    songs = get_all_songs()

    if not songs:
        flash('没有歌曲可下载')
        return redirect(url_for('index'))

    # Create ZIP file in memory
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for song in songs:
            face_id = song['face_id']
            role = song['uploaded_by']
            song_name = song['song_name']
            artist_part = f" - {song['artist']}" if song['artist'] else ""
            version_part = f" - v{song['version']}" if song['version'] else ""

            # Add MIDI file
            if song['midi_filename']:
                midi_path = os.path.join(app.config['UPLOAD_FOLDER'], song['midi_filename'])
                if os.path.exists(midi_path):
                    midi_name = f"{face_id:03d}{role} - {song_name}{artist_part}{version_part}.mid"
                    zf.write(midi_path, midi_name)

            # Add lyric file if exists
            if song['lyric_filename']:
                lyric_path = os.path.join(app.config['UPLOAD_FOLDER'], song['lyric_filename'])
                if os.path.exists(lyric_path):
                    lyric_name = f"{face_id:03d}{role} - {song_name}{artist_part}{version_part}.lrc"
                    zf.write(lyric_path, lyric_name)

    memory_file.seek(0)

    # Generate ZIP filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"吃得好好睡得饱饱_MIDI合集_{timestamp}.zip"

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)