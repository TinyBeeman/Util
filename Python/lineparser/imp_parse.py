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
t_RBRACKET = r'\]'
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


g_debug_lexer = False
g_lexer = lex.lex()

def verbose_level():
    return 1


class ImpException(Exception):
    pass

class ImpState:
    m_artist = None
    m_medium = None
    m_batch_size = 1
    m_batch_count = 1
    m_prompt_count = 1
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

    @property
    def prompt_count(self):
        return self.m_prompt_count
    
    @prompt_count.setter
    def prompt_count(self, value):
        self.m_prompt_count = value

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

class ParseNode:
    m_children = None
    m_last_value = None
    m_local_iteration = -1
    m_is_constant = None

    def __init__(self, type, children=None, leaf=None):
        self.m_type = type
        if children:
            self.m_children = children
        else:
            self.m_children = []
        self.m_leaf = leaf

    def insert_child(self, index, child):
        self.m_children.insert(index, child)

    def run_func(self, id, args, global_iteration, state):
        match id.lower():
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
            case 'update_b':
                return args[0]
            case _:
                return f"{id} Function Not Yet Implemented"
    
    def get_value_no_iteration(self, state: ImpState, global_iteration = 0, stack_depth=0 ):
        if (self.m_last_value != None):
            return self.m_last_value
        else:
            return self.process(state, global_iteration, stack_depth)

    # Returns true if this node's results never change
    def is_constant(self):
        if (self.m_is_constant is None):
            match self.m_type:
                case "func":
                    match self.m_leaf:
                        case 'rndi' | 'rnda' | 'nexta':
                            self.m_is_constant = False
                            self.m_is_constant
                case "id":
                    self.m_is_constant = False
                    return self.m_is_constant
                case 'constant' | 'list':
                    self.m_is_constant = True

            if (self.m_is_constant is None):
                for c in self.m_children:
                    if not c.is_constant():
                        self.m_is_constant = False

            if (self.m_is_constant is None):
                self.m_is_constant = True
        return self.m_is_constant

    def process_children(self, state, global_iteration, stack_depth):
        # No short circuiting for now
        processed_children = []
        try:
            for child in self.m_children:
                if (isinstance(child, ParseNode)):
                    processed_children.append(child.process(state, global_iteration, stack_depth+1))
                else:
                    processed_children.append(child)
        except TypeError as te:
            print(f"self.m_children is not iterable in {self.m_type}")
        return processed_children


    def process_this(self, processed_children, state: ImpState, global_iteration, stack_depth):
        res = None
        match self.m_type:
            case "func":
                res = self.run_func(self.m_leaf, processed_children[0], global_iteration, state)
            case "arglist":
                res = processed_children
            case "array":
                res = processed_children[0]
            case "id":
                match self.m_leaf:
                    case "batch_size":
                        res = state.batch_size
                    case "batch_count":
                        res =  state.batch_count
                    case "iteration":
                        res = global_iteration
                    case "prompt_count":
                        res = state.prompt_count
                    case _:
                        res = self.m_leaf
            case "constant":
                res = self.m_leaf    
            case "list":
                res = state.get_list(processed_children[0].lower())
            case "foreachargs":
                res = processed_children[0]
            case "passthru":
                res = processed_children[0]
            case _:
                print(f"Unknown Type {self.m_type}")
                res = processed_children[0]

        return res


    def process(self, state: ImpState, global_iteration, stack_depth=0):
        tab = ' ' * stack_depth
        leafstring = ('(' + str(self.m_leaf) + ')') if self.m_leaf is not None else ''
        nodestring = f"{self.m_type + leafstring} node"
        if (verbose_level() >= 2):
            print(f"{tab}Begin processing {nodestring}.")

        # Do we really need to run this again?
        if (self.m_last_value is None or not self.is_constant()):
            # Two short circuiting options:
            # update_b and update_c can cause us to skip
            # updating the children, so we want to do some special work to skip
            # and return the last used value.
            if (self.m_type == "func"):
                match self.m_leaf.lower():
                    case 'update_b':
                        if (global_iteration % state.batch_size != 0 and self.m_last_value != None):
                            return self.m_last_value
                    case 'update_c':
                        # We have to process the tree that represents c (2nds argument) early
                        # in case we don't want to process the first argument
                        # child 0 is arglist, child 1 is the second argument of arglist
                        c = self.m_children[0].m_children[1].process(state, global_iteration, stack_depth + 2)
                        if (global_iteration % c == 0):
                            self.m_last_value = self.m_children[0].m_children[0].process(state, global_iteration, stack_depth + 2)
                        return self.m_last_value

            processed_children = self.process_children(state, global_iteration, stack_depth)
            self.m_last_value = self.process_this(processed_children, state, global_iteration, stack_depth)
        
        if (verbose_level() >= 2):
                print(f"{tab}{nodestring} returning {self.m_last_value}")
        return self.m_last_value

    def describe_self(self):
        children = "[ "
        for c in self.m_children:
            children += c.describe_self()
        children += " ]"
        return f"ParseNode( { self.m_type }, leaf={ self.m_leaf }, children={children} )"
    

class ParseNodeRoot(ParseNode):
    
    # Passed by argument to foreach, determines the order this code snippet should be processed
    # TODO: Need to make use of this for using tags as well, most likely?
    m_index = 0 

    # The original order this code appears in the prompt
    m_original_index = 0

    # foreach arguments
    m_foreach_list_count: int = -1 # count of items in a foreach array
    m_foreach_repeat: int = 1 # Passed by argument, defaults to 1
    m_foreach_multiplier: int = 1 # Calculated value for how many times this should repeat itself due to other "foreach" statements
    

    def __init__(self, type, children=None, leaf=None):
        super().__init__(type, children, leaf)

    def get_foreach_args(self, state):
        args = len(self.m_children[0].m_children)
        list_count = 0
        repeat = 1
        index = 0
        lst = self.m_children[0].m_children[0].get_value_no_iteration(state)
        if (args >= 2):
            repeat = self.m_children[0].m_children[1].get_value_no_iteration(state)
        if (args >= 3):
            index = self.m_children[0].m_children[2].get_value_no_iteration(state)
        return [ lst, repeat, index ]

    def preprocess(self, state: ImpState, stack_depth=0):
        # foreach( array_cmd, [repeat = 1], [index = 0] )
        if self.m_type == "foreach":
            rg_args = self.get_foreach_args(state)
            print(rg_args[0])
            self.m_foreach_list_count = len(rg_args[0])
            self.m_foreach_repeat = rg_args[1]
            self.m_index = rg_args[2]
        else:
            self.m_foreach_list_count = 0
            self.m_foreach_repeat = 0
            self.m_index = 0

    def is_constant(self):
        if (self.m_type == 'foreach'):
            self.m_is_constant = False
            return False
        return super().is_constant()
    
    def run_func(self, id, args, global_iteration, state):
        if (id == "foreach"):
            args = self.get_foreach_args(state)
            lst = args[0]
            self.m_local_iteration = self.m_local_iteration + 1
            list_index = ( (self.m_local_iteration // (self.m_foreach_repeat * self.m_foreach_multiplier) ) % len(lst))
            return args[0][list_index]
        
        return super().run_func(id, args, global_iteration, state)
    
    def process_this(self, processed_children, state: ImpState, global_iteration, stack_depth):
        if (self.m_type == "foreach"):
            args = self.get_foreach_args(state)
            res = self.run_func("foreach", args, global_iteration, state)
            return res
        return super().process_this(processed_children, state, global_iteration, stack_depth)
    
    @property
    def foreach_list_count(self):
        return self.m_foreach_list_count

    @property
    def foreach_multiplier(self):
        return self.m_foreach_multiplier

    @foreach_multiplier.setter
    def foreach_multiplier(self, value: int):
        self.m_foreach_multiplier = value

    @property
    def foreach_repeat(self):
        return self.m_foreach_repeat

    @property
    def original_index(self):
        return self.m_original_index
    
    @original_index.setter
    def original_index(self, value: int):
        self.m_original_index = value

    @property
    def index(self):
        return self.m_index

    @property
    def sort_key(self):
        return 0xFF * self.index + self.original_index

def p_statement_expr(p):
    'statement : expression'
    p[0] = ParseNodeRoot("passthru", [ p[1] ] )

# foreach( array_cmd, [repeat = 1], [index = 0] )
def p_statement_foreach(p):
    'statement : FOREACH LPAREN foreachargs RPAREN'
    p[0] = ParseNodeRoot("foreach", [ p[3] ] )

def p_foreachargs_onearg(p):
    'foreachargs : expression'
    p[0] = ParseNode('foreachargs', [ p[1] ])

def p_foreachargs_twoarg(p):
    'foreachargs : expression COMMA NUMBER'
    p[0] = ParseNode('foreachargs', [ p[1], ParseNode("constant", [], p[3] ) ])

def p_foreachargs_threearg(p):
    'foreachargs : expression COMMA NUMBER COMMA NUMBER'
    p[0] = ParseNode('foreachargs', [ p[1], ParseNode("constant", [], p[3]), ParseNode("constant", [], p[5] ) ] )

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

# Arrays

def p_expression_array(p):
    'expression : array'
    p[0] = p[1]

def p_array(p):
    'array : LBRACKET arglist RBRACKET'
    p[0] = ParseNode("array", [ p[2]])

def p_expression_list(p):
    'array : LIST LPAREN expression RPAREN'
    p[0] = ParseNode("list", [ p[3] ] )


# Constants

def p_expression_constant(p):
    'expression : constant'
    p[0] = p[1]

def p_constant_string(p):
    'constant : STRING'
    p[0] = ParseNode("constant", [], p[1].strip('"') )

def p_constant_neg_number(p):
    'constant : MINUS NUMBER'
    p[0] = ParseNode("constant", [], -1 * p[1])

def p_constant_number(p):
    'constant : NUMBER'
    p[0] = ParseNode("constant", [], p[1] )


def p_error(p):
    print(f"Syntax error in input: {p}")

# Build the parser
g_parser = yacc.yacc()



class ImpCode:
    m_raw = ""
    m_tokens = None
    m_tree:ParseNodeRoot = None
    m_db = None
    m_orig_index = 0

    def __init__(self, raw_code, orig_index):
        global g_lexer
        global g_debug_lexer

        self.m_raw = raw_code
        self.m_tokens = []
        self.m_tree = None
        self.m_orig_index = orig_index

    def get_tokens(self):        
        if (len(self.m_tokens) == 0):
            g_lexer.input(self.m_raw)
            while True:
                tok = g_lexer.token()
                if not tok:
                    break
                self.m_tokens.append(tok)

        return self.m_tokens
    
    def get_raw_code(self):
        return self.m_raw
    
    def describe_self(self):
        s = f"Raw Code: {self.m_raw}\n" 
        for t in self.m_tokens:
            s += f"{str(t)};"
        s += "\n"
        return s        
    
    def get_parse_root(self) -> ParseNodeRoot:
        global g_parser
        if (self.m_tree is None):
            #try:
                self.m_tree = g_parser.parse(self.m_raw)
                self.m_tree.original_index = self.m_orig_index
            #except Exception as ex:
            #    print(f"Parse Exception parsing {self.m_raw}")
            #    print(type(ex))
            #    print(ex.args)
            #    print(ex)
        return self.m_tree


class ImpPrompt:
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
        i = 0
        for m in re.finditer(rx, self.m_raw):
            c = m.group('code')
            if (c is not None):
                self.m_codes.append(ImpCode(c, i))
                i += 1

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

        foreach_count = 1
        for c in self.m_codes:
            c.get_parse_root().preprocess(self.m_state)
        
        self.m_codes.sort(key=lambda code: code.get_parse_root().sort_key, reverse = True )
        
        for c in self.m_codes:
            rootnode:ParseNodeRoot = c.get_parse_root()
            if rootnode.foreach_list_count > 0:
                # Each successive for-each needs to hold its value as the previous for-each's iterate:
                # hence, the multiplier
                rootnode.foreach_multiplier = foreach_count
                foreach_count = foreach_count * rootnode.foreach_list_count * rootnode.foreach_repeat
                count = foreach_count

        prompts = []
        self.m_state.prompt_count = count
        for i in range(0, count):
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
            res = c.get_parse_root().process(self.m_state, iteration)
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
    # parser.raw_prompt = r'A {{rnda(list("medium"))}} by {{foreach(list("artist"), 3)}} of {{update_b(nexta(list("artist")))}} with {{rndi(1,5)}} heads.'
    parser.raw_prompt = r'A {{foreach(list(artist))}} by {{foreach(["a","b"], 4)}}, {{iteration}}/{{prompt_count}}.'
    parser.batch_size = 4
    parser.batch_count = 2
    # print(parser.get_token_prompt())
    prompts = parser.get_all_prompts()
    for i in range(0, len(prompts)):
        print(f"{str(i):>04}: {prompts[i]}")


test()
