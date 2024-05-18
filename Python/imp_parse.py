# impromptu parser

# fragment: any string appearing outside double braces (fragment{{code}}fragment{{code}}etc)
# code: any string appearing inside double braces

# Config Commands:
# seed(string) sets string per prompt

# Array Commands
# list(name) retrieves array from named list
# rngi(min, max, [step], [tag_name]) retrieves an array of values from min to max
# [val;val2;val3]: In place array, separated by semicolons

# Value Commands
# rndi(min, max, [tag_name]) returns a value (as string) from min to max (includes min and max), optimized version of randa(rngi(min, max))
# rnda(array_cmd, [tag_name]) returns a random value from an array
# nexta(array_cmd, [tag_name]) returns the next item in an array, starting with 0, wrapping around if needed
# update_i( value_cmd, [tag_name] ) calls cmd whenever prompt index changes (aka, every image)
# update_b( value_cmd, [tag_name] ) calls cmd for every new batch, previous value otherwise. (same as update_c( cmd, batch_size ))
# update_c( value_cmd, c ) calls cmd whenever the (prompt count % c) == 0, previous value otherwise
# string: Any string, including spaces can be a value. We will attempt to convert it to a number if needed.

# ForEach Command
# foreach( array_cmd, [repeat = 1], [index = 0], [tag=""] )
#   Creates new prompts, which means batch_count will be ignored.
#   The parser will walk through the current list of prompts, and repeat each item once (or more times if repeat > 1).
#   expands will be processed in the order of the indexes, then in order they appear in the list.
#   Tag can be used if the resulting string should appear elsewhere in the prompt, (by using the tag() function)


# tag( tag_name )

import re

example = 'A painting by {{rnd(list("artists"))}}, {{seed(())}}'

tokens = (
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'MINUS',
    'NUMBER',
    'ID'
)

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\['
t_ID   = r'[a-zA-Z_][a-zA-Z0-9_]*'


def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t
# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

import ply.lex as lex
lexer = lex.lex()

class ImpCode:
    m_raw = ""
    m_tokens = None

    def __init__(self, raw_code):
        global lexer

        self.m_raw = raw_code
        self.m_tokens = []
        lexer.input(self.m_raw)
        while True:
            tok = lexer.token()
            if not tok:
                break
            self.m_tokens.append(tok)

    def get_tokens(self):        
        return self.m_tokens
    
    def describe_self(self):
        s = f"Raw Code: {self.m_raw}\n" 
        for t in self.m_tokens:
            s += f"{str(t)};"
        s += "\n"
        return s        

class ImpParser:
    m_codes: list[str]
    m_raw: str

    def __init__(self):
        self.m_codes = []
        return
    
    def set_raw_prompt(self, raw_prompt):
        self.m_raw = raw_prompt
        self.m_codes = []
        # Add strings between {{ and }} to codes
        rx = r'{{(?P<code>([^}]|}[^}])*)}}'
        for m in re.finditer(rx, self.m_raw):
            c = m.group('code')
            if (c is not None):
                self.m_codes.append(ImpCode(c))        

    def get_raw_prompt(self):
        return self.m_raw
    
    def get_codes(self):
        return self.m_codes
    
    def describe_self(self):
        s = "PARSER:\n"
        s += f"Raw Prompt: {self.m_raw}\n"
        s += f"CODES\n----\n"
        for c in self.m_codes:
            s += c.describe_self()
        return s
            




def test():
    parser = ImpParser()
    parser.set_raw_prompt(r'A {{rnda(list(medium))}} by {{foreach(list(artist))}} of {{nexta("subject")}}')
    print(parser.describe_self())

test()
