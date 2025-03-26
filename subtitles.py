import os
import re
import datetime
import json
from database import MediaMetadata, update_or_store_media, store_subtitles
from paths import get_path

videos_directory = get_path("videos_directory")

class NoSuchTvSerie(Exception):
    pass

def get_file_extension(filename):
    split_tup = os.path.splitext(filename)
    return split_tup[1]

def parse_srt_time_range(timestamp: str):
    """
    Converts an SRT timestamp into start_time and end_time.

    Example:
    Input: "00:01:23,456 --> 00:01:25,789"
    Output: (datetime.time(0, 1, 23, 456000), datetime.time(0, 1, 25, 789000))
    """
    pattern = r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    match = re.match(pattern, timestamp)

    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())

    start_time = datetime.time(h1, m1, s1, ms1 * 1000)
    end_time = datetime.time(h2, m2, s2, ms2 * 1000)

    return start_time, end_time

# Function to load subtitles from an SRT file
def load_srt_subtitles(srt_file):
    with open(srt_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("in load_srt_subtitles file : ", srt_file)

    # Supprimer le BOM si présent
    if content.startswith('\ufeff'):
        content = content[1:]

    # Séparer les blocs de sous-titres
    blocks = re.split(r"\n\s*\n", content.strip())
    subtitles = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue  # Ignorer les blocs trop courts
        
        # La deuxième ligne est normalement le timestamp
        timestamp_line = lines[1].strip()
        
        # Vérifier le format du timestamp (doit contenir "-->")
        if "-->" not in timestamp_line:
            continue

        # Récupérer le texte
        text = "\n".join(lines[2:]).strip()

        subtitles.append({
            "timestamp": timestamp_line,
            "text": text,
        })

    return subtitles

def load_vtt_subtitles(vtt_file):
    with open(vtt_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    print("in load_subtitles file : ", vtt_file)

    # Supprimer le BOM si présent
    if content.startswith('\ufeff'):
        content = content[1:]

    # Supprimer la ligne WEBVTT si elle est présente
    lines = content.strip().split("\n")
    if lines[0].strip().upper() == "WEBVTT":
        lines = lines[1:]  # Ignorer la première ligne
    
    # Regrouper les lignes par blocs séparés par une ligne vide
    blocks = re.split(r"\n\s*\n", "\n".join(lines))
    subtitles = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue  # Ignorer les blocs trop courts
        
        # Vérifier si la première ligne est un timestamp
        if "-->" in lines[0]:
            timestamp = lines[0].strip()
            text = "\n".join(lines[1:]).strip()
        elif len(lines) > 1 and "-->" in lines[1]:  # Si la première ligne est un ID, alors le timestamp est à la deuxième ligne
            timestamp = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
        else:
            continue  # Ignorer les blocs mal formatés

        subtitles.append({
            "timestamp": timestamp,
            "text": text,
        })

    return subtitles

def store_vtt_subtitles(vtt_file, subtitles):
    with open(vtt_file, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for subtitle in subtitles:
            f.write(subtitle["timestamp"] + "\n")
            f.write(subtitle["french"] + "\n\n")
        f.close()

# Load Spanish and French subtitles

def load_subtitles(filename):
    ext = get_file_extension(filename)
    if ext == '.srt':
        return load_srt_subtitles(filename)
    elif ext == '.vtt':
        return load_vtt_subtitles(filename)
    else:
        print(f"In load_subtitles with filename: {filename} of extension {ext}")
        raise


def get_es_and_fr_subtitles_from_files(media: MediaMetadata):
    subtitles_directory = os.path.join(videos_directory, media.title) + " " + str(media.disc_number)
    print("videos_directory", videos_directory)
    spanish_subs_filename = os.path.join(subtitles_directory, media.spanish_subtitles_file)
    french_subs_filename = os.path.join(subtitles_directory, media.french_subtitles_file)
    print(spanish_subs_filename, french_subs_filename)
    long_spanish_subs_filename = os.path.join(subtitles_directory, media.long_spanish_subtitles_file)
    long_french_subs_filename = os.path.join(subtitles_directory, media.long_french_subtitles_file)
    print(spanish_subs_filename, french_subs_filename)
    spanish_subs = load_subtitles(spanish_subs_filename)
    french_subs = load_subtitles(french_subs_filename)
    long_spanish_subs = load_subtitles(long_spanish_subs_filename)
    long_french_subs = load_subtitles(long_french_subs_filename)

    # Merge Spanish and French subtitles
    #for es_sub, fr_sub in zip(spanish_subs, french_subs):
    #    es_sub["french"] = fr_sub["spanish"]  # Assign the translated text

    return spanish_subs, french_subs, long_spanish_subs, long_french_subs

def get_subtitles_context(dvd : int, directory=""):
    movies_directory = "Movies/Aquí No Hay Quien Viva 1/"
    context = {
        "es_subtitles" : os.path.join(movies_directory, "A1_t00_es.srt"),
        "fr_subtitles" : os.path.join(movies_directory, "A1_t00_fr.srt")
    }
    return context

def store_media(media: MediaMetadata):
    update_or_store_media(media)
    spanish_subs, french_subs, long_spanish_subs, long_french_subs = get_es_and_fr_subtitles_from_files(media)
    store_subtitles(media, "media", spanish_subs, french_subs)
    store_subtitles(media, "long", long_spanish_subs, long_french_subs)
