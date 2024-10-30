from html.parser import HTMLParser

class NotesParser(HTMLParser):

    def analyze(self, notes):
        self.notes = []
        self._buffer = ""
        self.feed(notes)

    def handle_starttag(self, tag, attrs):
        if tag == 'html':
            self._section = "html"
        elif tag == 'head':
            self._section = "head"
        elif tag == 'p':
            self._section = "paragraph"
            self._buffer = ""
            self._note_number_expected = True
        else:
            if self._section == "paragraph":
                self._buffer += f'<{tag}'
                for attr in attrs:
                    self._buffer += f""" {attr[0]}="{attr[1]}\""""
                self._buffer += '>'
            elif self._section == "head":
                self._buffer += f'<{tag}'
                for attr in attrs:
                    self._buffer += f""" {attr[0]}="{attr[1]}\""""
                self._buffer += '>'


    def handle_endtag(self, tag):
        if tag == 'head':
            self._section = ""
            self._head = self._buffer
        elif tag == 'p':
            try:
                note_number = int(self._note_number)
                self.notes.append((note_number, self._buffer))
                self._note_number = ''
            except:
                pass
        else:
            self._buffer += f'</{tag}>'

    def handle_data(self, data):
        if self._section == 'head':
            self._buffer += data
        elif self._section == "paragraph":
            if self._note_number_expected:
                self._note_number_expected = False
                self._note_number = data
            else:
                self._buffer += data
        else:
            print(self._section)
            raise