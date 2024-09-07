HTML_escape_characters = """
&#060   |   <   less than sign
&#064   |   @   at sign
&#093   |   ]   right bracket
&#123   |   {   left curly brace
&#125   |   }   right curly brace
&#133   |   …   ellipsis
&#135   |   ‡   double dagger
&#146   |   ’   right single quote
&#148   |   ”   right double quote
&#150   |   –   short dash
&#153   |   ™   trademark
&#162   |   ¢   cent sign
&#165   |   ¥   yen sign
&#169   |   ©   copyright sign
&#172   |   ¬   logical not sign
&#176   |   °   degree sign
&#178   |   ²   superscript 2
&#185   |   ¹   superscript 1
&#188   |   ¼   fraction 1/4
&#190   |   ¾   fraction 3/4
&#247   |   ÷   division sign
&#8221  |   ”   right double quote
&#062   |   >   greater than sign
&#091   |   [   left bracket
&#096   |   `   back apostrophe
&#124   |   |   vertical bar
&#126   |   ~   tilde
&#134   |   †   dagger
&#145   |   ‘   left single quote
&#147   |   “   left double quote
&#149   |   •   bullet
&#151   |   —   longer dash
&#161   |   ¡   inverted exclamation point
&#163   |   £   pound sign
&#166   |   ¦   broken vertical bar
&#171   |   «   double left than sign
&#174   |   ®   registered trademark sign
&#177   |   ±   plus or minus sign
&#179   |   ³   superscript 3
&#187   |   »   double greater-than sign
&#189   |   ½   fraction 1/2
&#191   |   ¿   inverted question mark
&#8220  |   “   left double quote
&#8212  |   —   dash"""

HTML_escape_characters_dict = {
    '"': '&#034;',
    '&': '&#038;',
    '\'': '&#039;',
    '<': '&#060;',
    '@': '&#064;',
    ']': '&#093;',
    '{': '&#123;',
    '|': '&#124;',
    '}': '&#125;',
    '…': '&#133;',
    '‡': '&#135;',
    '’': '&#146;',
    '”': '&#8221;',
    '–': '&#150;',
    '™': '&#153;',
    '¢': '&#162;',
    '¥': '&#165;',
    '©': '&#169;',
    '¬': '&#172;',
    '°': '&#176;',
    '²': '&#178;',
    '¹': '&#185;',
    '¼': '&#188;',
    '¾': '&#190;',
    '÷': '&#247;',
    '>': '&#062;',
    '[': '&#091;',
    '`': '&#096;',
    '~': '&#126;',
    '†': '&#134;',
    '‘': '&#145;',
    '“': '&#8220;',
    '•': '&#149;',
    '—': '&#8212;',
    '¡': '&#161;',
    '£': '&#163;',
    '¦': '&#166;',
    '«': '&#171;',
    '®': '&#174;',
    '±': '&#177;',
    '³': '&#179;',
    '»': '&#187;',
    '½': '&#189;',
    '¿': '&#191;'
    }
 

def convert_to_html_escape(str_to_convert : str):
    text = ""
    for char in str_to_convert:
        if char in HTML_escape_characters_dict:
            text += HTML_escape_characters_dict[char]
        else:
            text += char
    print(f"---- in convert_to_html_escape, returning {str_to_convert}" )
    return text

def convert_to_html_escape2(str_to_convert : str):
    res = ''.join(
    idx if idx not in HTML_escape_characters_dict else HTML_escape_characters_dict[idx] for idx in str_to_convert)
    return res