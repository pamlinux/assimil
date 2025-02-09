
from html.parser import HTMLParser

def findCTags():
    pass

class NotesParser(HTMLParser):

    def analyze(self, level, notes):
        self._level = level
        self._superscript_printed = False
        self.feed(notes)

    def handle_starttag(self, tag, attrs):
        self._tag = tag
        self._attrs = attrs

    def handle_data(self, data):
        if self._level == 0:
            if data == "patas arriba":
                print(f"""tag for "patas arriba" : {self._tag}""")
                print(f"""attrs for "patas arriba" : {self._attrs}""")
            elif data == "sens dessus-dessous":
                print(f"""tag for "sens dessus-dessous" : {self._tag}""")
                print(f"""attrs for "sens dessus-dessous" : {self._attrs}""")
            elif data == "as":
                print(f"""tag for "as" : {self._tag}""")
                print(f"""attrs for "as" : {self._attrs}""")
            elif data == "e":
                if not self._superscript_printed:
                    print(f"""tag for "e" : {self._tag}""")
                    print(f"""attrs for "e" : {self._attrs}""")
                    self._superscript_printed = True

                
        elif self._level == 1:
            if data == "el tuteo":
                print(f"""tag for "el tuteo" : {self._tag}""")
                print(f"""attrs for "el tuteo" : {self._attrs}""")
            elif data == "le tutoiement":
                print(f"""tag for "le tutoiement" : {self._tag}""")
                print(f"""attrs for "le tutoiement" : {self._attrs}""")
            elif data == "como":
                print(f"""tag for "como" : {self._tag}""")
                print(f"""attrs for "como" : {self._attrs}""")

 