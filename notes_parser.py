from html.parser import HTMLParser

class NotesParser(HTMLParser):

    def analyze(self, notes):
        self._paragraph = ""
        self.notes = []
        self.feed(notes)

    def handle_starttag(self, tag, attrs):
        if tag == 'html':
            self._section = "html"
        elif tag == 'head':
            self._head = ""
            self._section = "head"
        elif tag == 'p':
            self._section = "paragraph"
            self._paragraph = ""
            self._note_number_expected = True
        else:
            if self._section == "paragraph":
                self._paragraph += f'<{tag}'
                for attr in attrs:
                    self._paragraph += f" {attr[0]}={attr[1]}"
                self._paragraph += '>'
            elif self._section == "head":
                self._head += f'<{tag}'
                for attr in attrs:
                    self._head += f" {attr[0]}={attr[1]}"
                self._head += '>'


    def handle_endtag(self, tag):
        if tag == 'head':
            self._section = ""
        elif tag == 'p':
            try:
                note_number = int(self._note_number)
                self.notes.append((note_number, self._paragraph))
                self._note_number = ''
            except:
                pass
        else:
            self._paragraph += f'</{tag}>'

    def handle_data(self, data):
        if self._section == 'head':
            self._head += data
        elif self._section == "paragraph":
            if self._note_number_expected:
                self._note_number_expected = False
                self._note_number = data
            else:
                self._paragraph += data
        else:
            print(self._section)
            raise