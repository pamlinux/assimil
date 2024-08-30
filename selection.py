from html.parser import HTMLParser

class MarkedLinesParser(HTMLParser):
    def analyze_lesson(self, lesson):
        self.sentences = []
        self.marked_lines = []
        self.marked_lines_numbers = {}
        self.current_line_number = 0
        self.feed(lesson)

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current_sentence = ""
        elif tag == "mark":
            if not self.current_line_number in self.marked_lines_numbers:
                self.marked_lines_numbers[self.current_line_number] = True
            self.current_sentence += f"<{tag}>"
        else:
            self.current_sentence += f"<{tag}>"
        

    def handle_endtag(self, tag):
        if tag == "p":
            self.sentences.append(self.current_sentence.strip())
            self.current_line_number += 1
        else:
            self.current_sentence += f"</{tag}>"

    def handle_data(self, data):
        if hasattr(self, "current_sentence"):
            self.current_sentence += data
    
    def get_marked_lines_numbers(self):
        return self.marked_lines_numbers

    def get_sentences(self):
        return self.sentences
    
parser = MarkedLinesParser()
    
def extract_selection(lesson):
    parser.analyze_lesson(lesson)
    marked_lines_numbers = parser.get_marked_lines_numbers()
    sentences = parser.get_sentences()
    return marked_lines_numbers, sentences
    
def extract_paragraphs(lesson):
    parser.analyze_lesson(lesson)
    return parser.get_sentences()
