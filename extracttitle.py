import eyed3
import os
from pathlib import Path

def get_title(filename):
    audiofile = eyed3.load(filename)
    return audiofile.tag.title

def get_directory_filenames(root_directory):
    w = os.walk(root_directory)
    fn = []
    for (dirpath, dirnames, filenames) in w:
        fn.extend(filenames)
    return fn

def get_sentences(lesson_directory):
    w = os.walk(lesson_directory)
    fn = []
    sentences = []
    for (dirpath, dirnames, filenames) in w:
        for fn in filenames:
            print(dirpath, fn)
            sentences.append(get_title(os.path.join(dirpath, fn)))
    return sentences
    
    

def get_lessons(root_directory):
    get_directory_filenames(root_directory)

if __name__ == '__main__':
    title = get_title("S01.mp3")
    print(title)
    lessons_list = get_lessons("FULL Lessons")
    sentences = get_sentences("Sentences/L001-Spanish ASSIMIL")
    print(sorted(sentences))
    
