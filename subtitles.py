import os
import re
import datetime
import json
from schemas.media import MediaMetadata
from database import update_or_store_media, store_subtitles, get_media_metadata
import ffmpeg
import whisper
import logging
from pathlib import Path
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

def get_audio_codec(video_path: str) -> str:
    """Récupère le codec audio d'un fichier vidéo à l'aide de ffprobe."""
    try:
        probe_result = ffmpeg.probe(video_path)
        audio_stream = next(
            (stream for stream in probe_result["streams"] if stream["codec_type"] == "audio"), None
        )
        if audio_stream:
            return audio_stream["codec_name"]
        else:
            raise ValueError("Aucun flux audio trouvé dans le fichier vidéo.")
    except ffmpeg.Error as e:
        logging.error(f"Erreur FFmpeg lors de la récupération du codec audio : {e}")
        raise

def extract_audio(video_path: str, audio_path: str, audio_format: str = "wav"):
    """Extrait la piste audio d'un fichier vidéo."""
    try:
        logging.info(f"Extraction de l'audio de {video_path} vers {audio_path}")
        if audio_format == "wav":
            ffmpeg.input(video_path).output(
                audio_path, format="wav", acodec="pcm_s16le", ar="16000", loglevel="error"
            ).run(overwrite_output=True)
        else:
            ffmpeg.input(video_path).output(
                audio_path, format=audio_format, acodec="copy", loglevel="error"
            ).run(overwrite_output=True)
    except ffmpeg.Error as e:
        logging.error(f"Erreur FFmpeg lors de l'extraction de l'audio : {e.stderr.decode('utf-8')}")
        raise

def write_srt(segments: list, filename: str):
    """Écrit les segments de transcription au format SRT."""
    with open(filename, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            # Convertir les secondes en format SRT (HH:MM:SS,MS)
            start_h = int(start / 3600)
            start_m = int((start % 3600) / 60)
            start_s = int(start % 60)
            start_ms = int((start - int(start)) * 1000)
            end_h = int(end / 3600)
            end_m = int((end % 3600) / 60)
            end_s = int(end % 60)
            end_ms = int((end - int(end)) * 1000)
            f.write(f"{i+1}\n")
            f.write(f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> {end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n")
            f.write(f"{text}\n\n")

def generate_all_subtitle_files(video_path: str):
    """
    Génère des fichiers de sous-titres à partir d'une vidéo en utilisant ffmpeg-python et whisper.
    """
    video_file = Path(video_path)
    base = video_file.with_suffix("")
    audio_codec = get_audio_codec(str(video_file))  # obtenir le codec audio
    audio_format = "wav" if audio_codec == "pcm_s16le" else audio_codec  # si wav, on garde pcm_s16le
    audio_file = base.with_name(f"{base.name}_audio.{audio_format}")  # ajuster l'extension
    srt_es = str(base.with_name(f"{base.name}_audio_es.srt"))
    srt_fr = str(base.with_name(f"{base.name}_audio_fr.srt"))
    vtt_es = str(base.with_name(f"{base.name}_audio_es.vtt"))

    try:
        # 1. Extraire l'audio avec ffmpeg-python
        extract_audio(str(video_file), str(audio_file), audio_format)  # passer le format audio

        # 2. Transcrire en espagnol avec Whisper
        logging.info(f"Transcription en espagnol de : {audio_file} vers {srt_es}")
        model = whisper.load_model("medium")
        result_es = model.transcribe(str(audio_file), language="es") # Pas de output_format
        write_srt(result_es["segments"], srt_es) # Utiliser la fonction pour écrire le SRT


        # 3. Traduire en français avec Whisper
        logging.info(f"Traduction en français de : {audio_file} vers {srt_fr}")
        result_fr = model.transcribe(str(audio_file), language="es", task="translate")
        write_srt(result_fr["segments"], srt_fr) # Utiliser la fonction pour écrire le SRT

        # 4. Convertir .srt en .vtt avec ffmpeg-python
        logging.info(f"Conversion de : {srt_es} vers {vtt_es}")
        ffmpeg.input(srt_es).output(vtt_es, loglevel="error").run(overwrite_output=True)

        return {
            "audio": str(audio_file),
            "srt_es": srt_es,
            "srt_fr": srt_fr,
            "vtt_es": vtt_es,
        }
    except Exception as e:
        logging.error(f"La génération des sous-titres a échoué : {e}")
        raise


def get_subtitles_path(subtitle_type: str, language: str, media_id):
    print("videos_directory", videos_directory)
    media_metadata = get_media_metadata(media_id)
    video_directory = os.path.join(videos_directory, media_metadata.title) + " " + str(media_metadata.disc_number)
    video_path = os.path.join(video_directory, media_metadata.video_filename)
    video_file = Path(video_path)
    base = video_file.with_suffix("")
    if subtitle_type == "media":
        type_addendum = ""
    elif  subtitle_type == "long":
        type_addendum = "audio_"
    else:
        raise

    return str(base.with_name(f"{base.name}_{type_addendum}{language}.srt"))

def store_subtitles_from_files_for_media_type(media_id: int, subtitle_type: str):
    srt_filename_es = get_subtitles_path(subtitle_type, "es", media_id)
    srt_filename_fr = get_subtitles_path(subtitle_type, "fr", media_id)

    spanish_subs = load_subtitles(srt_filename_es)
    french_subs = load_subtitles(srt_filename_fr)

    store_subtitles(media_id, subtitle_type, spanish_subs, french_subs)

def store_subtitles_from_files(media_id: int):
    store_subtitles_from_files_for_media_type(media_id, "media")
    store_subtitles_from_files_for_media_type(media_id, "long")


def store_media(media: MediaMetadata):
    print(media)
    media_id = update_or_store_media(media)
    print(f"In store_media with media of id: {media_id}")
 #   try:
    video_directory = os.path.join(videos_directory, media.title) + " " + str(media.disc_number)
    print("videos_directory", videos_directory)
    video_path = os.path.join(video_directory, media.video_filename)
    print(f"vidéo path : {video_path}")
    #result = generate_all_subtitle_files(video_path)
    #print(result)
    store_subtitles_from_files(media_id)
#    except Exception as e:
#        logging.error(f"Erreur lors de l'exécution du script : {e}")

def get_subtitle_vtt_path(media_id: int):
    media_metadata = get_media_metadata(media_id)
    video_directory = os.path.join(videos_directory, media_metadata.title) + " " + str(media_metadata.disc_number)
    video_path = os.path.join(video_directory, media_metadata.video_filename)
    video_file = Path(video_path)
    base = video_file.with_suffix("")
    return str(base.with_name(f"{base.name}_es.vtt"))

def get_video_path(media_id: int):
    print("videos_directory", videos_directory)
    media_metadata = get_media_metadata(media_id)
    video_directory = os.path.join(videos_directory, media_metadata.title) + " " + str(media_metadata.disc_number)
    video_path = os.path.join(video_directory, media_metadata.video_filename)
    video_file = Path(video_path)
    base = video_file.with_suffix("")

    return str(base.with_name(f"{base.name}.m4v"))
