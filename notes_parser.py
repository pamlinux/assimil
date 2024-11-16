from html.parser import HTMLParser

class NotesParser(HTMLParser):

    def analyze(self, notes):
        self._buffer = ""
        self._in_lesson_title = False
        self._lessons = []
        self.feed(notes)
        self._lessons.append((self._lesson_nb, self._notes))

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
            if self._in_lesson_title:
                self._buffer = ""
                self._in_lesson_title = False
                self._notes = []
            else:
                try:
                    note_number = int(self._note_number)
                    self._notes.append((note_number, self._buffer.strip()))
                    self._note_number = ''
                except:
                    pass
        else:
            self._buffer += f'</{tag}>'

    def handle_data(self, data):
        print(data)
        if self._section == 'head':
            self._buffer += data
        elif self._section == "paragraph":
            index = data.find('Notes')
            if index == 0:
                if hasattr(self, "_lesson_nb"):
                    self._lessons.append((self._lesson_nb, self._notes))
                self._lesson_nb = int(data[5:])
                self._in_lesson_title = True
            else:
                if data and not data.isspace():
                    if self._note_number_expected:
                        self._note_number_expected = False
                        self._note_number = data
                    else:
                        self._buffer += data
        else:
            print(self._section)
            raise
    
    def get_notes(self):
        return self._lessons
    