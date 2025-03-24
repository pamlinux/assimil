import os
import re
import json

class NoSuchTvSerie(Exception):
    pass
    
# Function to load subtitles from an SRT file
def load_srt_subtitles(srt_file):
    with open(srt_file, "r", encoding="utf-8") as f:
        content = f.read()
        print("in load_subtitles file : ", f)
        if content[0] == '\ufeff':
            content = content[1:]
    # Split into subtitle blocks
    blocks = re.split(r"\n\s*\n", content.strip())
    subtitles = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        
        index = lines[0].strip()
        timestamp = lines[1].strip()
        text = "\n".join(lines[2:])

        subtitles.append({
            "id": index,
            "timestamp": timestamp,
            "spanish": text,
            "french": text  # Placeholder for translation
        })

    return subtitles

def load_vtt_subtitles(vtt_file):
    with open(vtt_file, "r", encoding="utf-8") as f:
        content = f.read()
        print("in load_subtitles file : ", f)
        if content[0] == '\ufeff':
            content = content[1:]
    # Split into subtitle blocks
    blocks = re.split(r"\n\s*\n", content.strip())
    subtitles = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 2:
            continue
        
        timestamp = lines[1].strip()
        text = "\n".join(lines[2:])

        subtitles.append({
            "timestamp": timestamp,
            "spanish": text,
            "french": ""  # Placeholder for translation
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

def get_es_and_fr_subtitles_from_files(dvd: int, format: str = 'srt', source = ""):
    movies_directory = "./Movies/Aquí No Hay Quien Viva 1/"
    spanish_subs_filename = os.path.join(movies_directory, f"A{str(dvd)}_t00_es{source}.{format}")
    french_subs_filename = os.path.join(movies_directory, f"A{str(dvd)}_t00_fr{source}.{format}")
    print(spanish_subs_filename, french_subs_filename)
    if format == 'srt':
        spanish_subs = load_srt_subtitles(spanish_subs_filename)
        french_subs = load_srt_subtitles(french_subs_filename)
    elif format == 'vtt':
        spanish_subs = load_vtt_subtitles(spanish_subs_filename)
        french_subs = load_vtt_subtitles(french_subs_filename)
    # Merge Spanish and French subtitles
    for es_sub, fr_sub in zip(spanish_subs, french_subs):
        es_sub["french"] = fr_sub["spanish"]  # Assign the translated text

    return spanish_subs

def get_subtitles_context(dvd : int, directory=""):
    movies_directory = "Movies/Aquí No Hay Quien Viva 1/"
    context = {
        "es_subtitles" : os.path.join(movies_directory, "A1_t00_es.srt"),
        "fr_subtitles" : os.path.join(movies_directory, "A1_t00_fr.srt")
    }
    return context
