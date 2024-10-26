from html.parser import HTMLParser

class NotesParser(HTMLParser):

    def analyze(self, notes):
        self._paragraph = ""
        self.notes = []
        self.feed(notes)

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self._paragraph = ""
        else:
            self._paragraph += f'<{tag}'
            for attr in attrs:
                self._paragraph += f" {attr[0]}={attr[1]}"
            self._paragraph += '>'
            #print(f"for tag {tag}, attrs :{attrs}")
    def handle_endtag(self, tag):
        if tag == 'p':
            self.notes.append(self._paragraph)
        else:
            self._paragraph += f'</{tag}>'

    def handle_data(self, data):
        self._paragraph += data
