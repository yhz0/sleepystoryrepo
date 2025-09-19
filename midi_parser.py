"""
MIDI file parsing utilities for track name extraction and analysis.
Handles Unicode encoding issues and provides clean track information.
"""

import mido


def parse_midi_tracks(filepath):
    """
    Parse MIDI file and extract track names, intelligently handling the first track.
    Skips the first track only if it contains no musical notes (metadata only).

    Args:
        filepath (str): Path to the MIDI file

    Returns:
        list: List of track names from musical tracks
    """
    try:
        mid = mido.MidiFile(filepath)
        track_names = []

        # Check if first track has notes
        if len(mid.tracks) > 0:
            first_track_has_notes = _track_has_notes(mid.tracks[0])
        else:
            return []

        # Determine which tracks to process
        if first_track_has_notes:
            # Include all tracks starting from index 0
            tracks_to_process = enumerate(mid.tracks, 1)
        else:
            # Skip first track (metadata only), start from index 1
            tracks_to_process = enumerate(mid.tracks[1:], 1)

        # Process the selected tracks
        for i, track in tracks_to_process:
            track_name = f"Track {i}"

            # Look for track_name messages in the track
            for msg in track:
                if msg.type == 'track_name' and hasattr(msg, 'name') and msg.name.strip():
                    # Clean the track name to handle encoding issues
                    clean_name = _clean_track_name(msg.name.strip())
                    if clean_name:
                        track_name = clean_name
                    break

            track_names.append(track_name)

        return track_names

    except Exception as e:
        print(f"Error parsing MIDI file {filepath}: {e}")
        return []


def _track_has_notes(track):
    """
    Check if a MIDI track contains any musical notes.

    Args:
        track: MIDI track object

    Returns:
        bool: True if track contains note_on or note_off messages, False otherwise
    """
    for msg in track:
        if msg.type in ['note_on', 'note_off']:
            return True
    return False


def _clean_track_name(name):
    """
    Clean track name to handle encoding issues and filter out problematic characters.

    Args:
        name (str): Raw track name from MIDI file

    Returns:
        str: Cleaned track name, or empty string if too problematic
    """
    if not name:
        return ""

    try:
        # Try to encode/decode to catch encoding issues
        cleaned = name.encode('utf-8', errors='ignore').decode('utf-8')

        # Filter out tracks that are mostly non-ASCII or control characters
        printable_chars = sum(1 for c in cleaned if c.isprintable())
        if len(cleaned) > 0 and printable_chars / len(cleaned) < 0.7:
            # If less than 70% of characters are printable, consider it problematic
            return ""

        return cleaned

    except Exception:
        return ""


def get_midi_info(filepath):
    """
    Get comprehensive information about a MIDI file.

    Args:
        filepath (str): Path to the MIDI file

    Returns:
        dict: Dictionary containing MIDI file information
    """
    try:
        mid = mido.MidiFile(filepath)

        info = {
            'total_tracks': len(mid.tracks),
            'ticks_per_beat': mid.ticks_per_beat,
            'length': mid.length,
            'track_names': parse_midi_tracks(filepath)
        }

        return info

    except Exception as e:
        print(f"Error getting MIDI info for {filepath}: {e}")
        return {
            'total_tracks': 0,
            'ticks_per_beat': 0,
            'length': 0,
            'track_names': []
        }