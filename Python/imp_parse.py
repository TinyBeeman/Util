# impromptu parser

# fragment: any string appearing outside double braces (fragment{{code}}fragment{{code}}etc)
# code: any string appearing inside double braces

# Config Commands:
# seed(string) sets string per prompt

# Array Commands
# list("name") retrieves array from named list
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



class IPar:
    def get_code(self, s):
        codes = []
        rx = r'{{(?P<code>([^}]|}[^}])*)}}'
        for m in re.finditer(rx, s):
            c = m.group('code')
            if (c is not None):
                codes.append(c)



def test():
    s = r'This is a test of using { and } to detect {{ sections of code contained in the { and }}} and extract them'

