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
import ply.lex as lex
import ply.yacc as yacc
import random
import enum


class ImpState:
    m_artist = None
    m_medium = None
    m_batch_size = 1
    m_batch_count = 1
    m_vars = None

    def __init__(self):
        self.m_artist = [ "Van Gogh", "Norman Rockwell", "Alphonse Mucha", "Edward Hopper" ]
        self.m_medium = [ "Oil Painting", "Sculpture", "Photo", "Watercolor", "Acrylic"]
        self.m_vars = {} 

    @property
    def batch_size(self):
        return self.m_batch_size
    
    @batch_size.setter
    def batch_size(self, value):
        self.m_batch_size = value

    @property
    def batch_count(self):
        return self.m_batch_count
    
    @batch_count.setter
    def batch_count(self, value):
        self.m_batch_count = value

    def check_args(args, allowed):
        if (isinstance(allowed, list)):
            for a in allowed:
                if a == len(args):
                    return True
        else:
            if allowed == len(args):
                return True
        return False
    
    def set_var(self, key, value):
        self.m_vars[key] = value
    
    def get_var(self, key):
        return self.m_vars[key]
    
    def get_list(self, name):
        match name:
            case "artist":
                return self.m_artist
            case "medium":
                return self.m_medium
        return [ "Missing List " + name ]


reserved = {
   'list' : 'LIST',
   'foreach' : 'FOREACH'
}

tokens = [
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'MINUS',
    'NUMBER',
    'STRING',
    'ID',
    'COMMA',
] + list(reserved.values())

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_STRING = r'".*?"'
t_LBRACKET = r'\['
t_RBRACKET = r'\['
t_COMMA = r','


def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value,'ID')
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


g_lexer = lex.lex()

def verbose_level():
    return 1

class StatementType(enum.IntEnum):
    NONE = enum.auto()
    SIMPLE = enum.auto()
    FOREACH = enum.auto()

class ParseNode:
    m_children = None
    m_last_value = None
    m_local_iteration = -1

    def __init__(self, type, children=None, leaf=None):
        self.m_type = type
        if children:
            self.m_children = children
        else:
            self.m_children = []
        self.m_leaf = leaf

    def insert_child(self, index, child):
        self.m_children.insert(index, child)

    def get_statement_type(self):
        if (self.m_type == "func" and self.m_leaf.lower() == "foreach"):
            return StatementType.FOREACH

        for c in self.m_children:
            if c.get_statement_type() == StatementType.FOREACH:
                return StatementType.FOREACH
        
        return StatementType.SIMPLE

    def run_func(self, id, args, global_iteration, state):
        match id.lower():
            case 'foreach':
                # foreach( array_cmd, [repeat = 1], [index = 0] )
                lst = args[0]
                argc = len(args)
                repeat = args[1] if (argc >= 2) else 1

                self.m_local_iteration = self.m_local_iteration + 1
                list_index = ( (self.m_local_iteration // repeat) % len(lst))
                return args[0][list_index]
            case 'nexta':
                # nexta(array_cmd, [tag_name]) returns the next item in an array, starting with 0, wrapping around if needed
                self.m_local_iteration = self.m_local_iteration + 1
                lst = args[0]
                index = self.m_local_iteration % len(lst)
                return args[0][index]
            case 'rnda':
                list_size = len(args[0])
                return args[0][random.randint(0, list_size-1)]
            case 'rndi':
                min = int(args[0])
                max = int(args[1])
                return random.randint(min, max)
            case 'update_c':
                return args[0]
            
            
# update_b( value_cmd, [tag_name] ) calls cmd for every new batch, previous value otherwise. (same as update_c( cmd, batch_size ))
# update_c( value_cmd, c, [tag_name] ) calls cmd whenever the (prompt count % c) == 0, previous value otherwise

            case _:
                return f"{id} Function Not Yet Implemented"

    
    def get_foreach_args(self, state):
        args = len(self.m_children[0].m_children)
        list_count = 0
        repeat = 1
        index = 0
        lst = self.m_children[0].m_children[0].get_value_no_iteration(state)
        list_count = len(lst)
        if (args >= 2):
            repeat = self.m_children[0].m_children[1].get_value_no_iteration(state)
        if (args >= 3):
            index = self.m_children[0].m_children[2].get_value_no_iteration(state)
        return [ lst, repeat, index ]

    def preprocess(self, state: ImpState, stack_depth=0):
        # foreach( array_cmd, [repeat = 1], [index = 0] )
        if self.m_type == "foreach":
            # assert(self.m_children[0].m_type == "foreachargs")
            # Expression: self.m_children[0].m_children[0]
            rg_args = self.get_foreach_args(state)
            return [ len(rg_args[0]), rg_args[1], rg_args[2] ]
        else:
            return [0,0,0]

    def get_value_no_iteration(self, state: ImpState, global_iteration = 0, stack_depth=0 ):
        if (self.m_last_value != None):
            return self.m_last_value
        else:
            return self.process(state, global_iteration, stack_depth)

    def process(self, state: ImpState, global_iteration, stack_depth=0):
        pchildren = []
        leafstring = ('(' + str(self.m_leaf) + ')') if self.m_leaf is not None else ''
        nodestring = f"{self.m_type + leafstring} node"
        tab = ' ' * stack_depth
        
        
        if (verbose_level() >= 2):
            print(f"{tab}Begin processing {nodestring}.")

        # skip update_b and update_c processing of children if needed.
        if (self.m_type == "func"):
            match self.m_leaf.lower():
                case 'update_b':
                    if (global_iteration % state.batch_size == 0):
                        self.m_last_value = self.m_children[0].m_children[0].process(state, global_iteration, stack_depth + 2)
                    return self.m_last_value
                case 'update_c':
                    # We have to process the tree that represents c early
                    # HACK
                    c = self.m_children[0].m_children[1].process(state, global_iteration, stack_depth + 2)
                    # c = self.m_children[1].process(state, global_iteration, stack_depth + 1)-
                    if (global_iteration % c == 0):
                        self.m_last_value = self.m_children[0].m_children[0].process(state, global_iteration, stack_depth + 2)
                    return self.m_last_value

        # No short circuiting for now
        try:
            for child in self.m_children:
                if (isinstance(child, ParseNode)):
                    pchildren.append(child.process(state, global_iteration, stack_depth+1))
                else:
                    pchildren.append(child)
        except TypeError as te:
            print(f"self.m_children is not iterable in {self.m_type}")

        res = None
        match self.m_type:
            case "func":
                # arglist in pchildren[0]
                res = self.run_func(self.m_leaf, pchildren[0], global_iteration, state)
            case "arglist":
                res = pchildren
            case "id":
                res = self.m_leaf
            case "neg_number":
                res = -1 * self.m_leaf
            case "number":
                res = self.m_leaf
            case "string":
                res = self.m_leaf
            case "list":
                res = state.get_list(pchildren[0].lower())
            case "foreach":
                args = self.get_foreach_args(state)
                res = self.run_func("foreach", args, global_iteration, state)
            case _:
                res = pchildren[0]

        if (verbose_level() >= 2):
            print(f"{tab}{nodestring} returning {res}")

        self.m_last_value = res
        return res


    def describe_self(self):
        children = "[ "
        for c in self.m_children:
            children += c.describe_self()
        children += " ]"
        return f"ParseNode( { self.m_type }, leaf={ self.m_leaf }, children={children} )"

def p_statement_expr(p):
    'statement : expression'
    p[0] = p[1]

# foreach( array_cmd, [repeat = 1], [index = 0] )
def p_statement_foreach(p):
    'statement : FOREACH LPAREN foreachargs RPAREN'
    p[0] = ParseNode("foreach", [ p[3] ] )

def p_foreachargs_onearg(p):
    'foreachargs : array'
    p[0] = ParseNode('foreachargs', [ p[1] ])

def p_foreachargs_twoarg(p):
    'foreachargs : array COMMA NUMBER'
    p[0] = ParseNode('foreachargs', [ p[1], ParseNode("number", [], p[3] ) ])

def p_foreachargs_threearg(p):
    'foreachargs : array COMMA NUMBER COMMA NUMBER'
    p[0] = ParseNode('foreachargs', [ p[1], ParseNode("number", [], p[3]), ParseNode("number", [], p[5] ) ] )

def p_expression_array(p):
    'expression : array'
    p[0] = ParseNode("array", [ p[1] ] )

def p_array_list(p):
    'array : LIST LPAREN expression RPAREN'
    p[0] = ParseNode("list", [ p[3] ] )

def p_array_const(p):
    'array : LBRACKET arglist RBRACKET'
    p[0] = ParseNode("const_array", [ p[2] ])

def p_expression_string(p):
    'expression : STRING'
    p[0] = ParseNode("string", [], p[1].strip('"') )

def p_negative_number(p):
    'expression : MINUS NUMBER'
    p[0] = ParseNode("number", [], -1 * p[1])

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = ParseNode("number", [], p[1] )

def p_expression_id(p):
    'expression : ID'
    p[0] = ParseNode("id", [], p[1])

def p_expression_func(p):
    'expression : ID LPAREN arglist RPAREN'
    p[0] = ParseNode("func", [ p[3] ], p[1] )

def p_arglist_args(p):
    'arglist : expression COMMA arglist'
    p[3].insert_child(0, p[1])
    p[0] = p[3]

def p_arglist_expr(p):
    'arglist : expression'
    p[0] = ParseNode("arglist", [ p[1] ])

def p_error(p):
    print(f"Syntax error in input: {p}")

# Build the parser
g_parser = yacc.yacc()



class ImpCode:
    m_raw = ""
    m_tokens = None
    m_tree = None
    m_db = None

    def __init__(self, raw_code):
        global g_lexer

        self.m_raw = raw_code
        self.m_tokens = []
        self.m_tree = None

        g_lexer.input(self.m_raw)
        while True:
            tok = g_lexer.token()
            if not tok:
                break
            self.m_tokens.append(tok)

    def get_tokens(self):        
        return self.m_tokens
    
    def get_raw_code(self):
        return self.m_raw
    
    def describe_self(self):
        s = f"Raw Code: {self.m_raw}\n" 
        for t in self.m_tokens:
            s += f"{str(t)};"
        s += "\n"
        return s        
    
    def get_tree(self):
        global g_parser
        if (self.m_tree is None):
            self.m_tree = g_parser.parse(self.m_raw)
        return self.m_tree


class Imprompt:
    m_prompt: str = ""
    m_seed: int = -1

    def __init__(self, prompt, seed):
        self.m_prompt = prompt
        self.m_seed = seed

    @property
    def prompt(self) -> str:
        return self.m_prompt
    
    @prompt.setter
    def prompt(self, value: str):
        self.m_prompt = value

    @property
    def seed(self) -> int:
        return self.m_seed
    
    @seed.setter
    def seed(self, value: int):
        self.m_seed = value


class ImpParser:
    m_codes: list[ImpCode]
    m_raw: str
    m_state: ImpState = None

    def __init__(self):
        self.m_codes = []
        self.m_state = ImpState()
        self.m_state.batch_count = 2
        self.m_state.batch_size = 4
        return
    
    @property
    def raw_prompt(self):
        return self.m_raw
    
    @raw_prompt.setter
    def raw_prompt(self, value):
        self.m_raw = value
        self.m_codes = []
        # Add strings between {{ and }} to codes
        rx = r'{{(?P<code>([^}]|}[^}])*)}}'
        for m in re.finditer(rx, self.m_raw):
            c = m.group('code')
            if (c is not None):
                self.m_codes.append(ImpCode(c))        

    @property
    def batch_size(self):
        return self.m_state.batch_size
    
    @batch_size.setter
    def batch_size(self, value):
        self.m_state.batch_size = value
    
    def get_codes(self):
        return self.m_codes
    
    def get_all_prompts(self):
        count = self.m_state.batch_size * self.m_state.batch_count
        prompts = []
        for i in range(0, count - 1):
            prompts.append(self.produce_prompt(i))
        return prompts

    def get_token_prompt(self):
        output = self.m_raw
        for c in self.m_codes:
            res = " ".join(str(x) for x in c.get_tokens())
            raw = "{{" + c.get_raw_code() + "}}"
            output = output.replace(raw, str(res))
        return output

    def produce_prompt(self, iteration):
        output = self.m_raw
        for c in self.m_codes:
            res = c.get_tree().process(self.m_state, iteration)
            raw = "{{" + c.get_raw_code() + "}}"
            output = output.replace(raw, str(res))
        return output


    def describe_self(self):
        s = "PARSER:\n"
        s += f"Raw Prompt: {self.m_raw}\n"
        s += f"CODES\n----\n"
        for c in self.m_codes:
            s += c.describe_self()
        return s

def test():
    parser = ImpParser()
    parser.raw_prompt = r'A {{rnda(list("medium"))}} by {{foreach(list("artist"), 4)}} of {{update_c(nexta(list("artist")), 2)}} with {{rndi(1,5)}} heads.'
    parser.batch_size = 4
    parser.batch_count = 2
    # print(parser.get_token_prompt())
    prompts = parser.get_all_prompts()
    for p in prompts:
        print(p)


test()
