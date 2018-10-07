"""
<Started>
  September 2018

<Author>
  Alan Cao

<Purpose>
  This module holds a set of methods to parse a trace serialized as an AST.

  The path to a file generated must be passed to the constructor method 
  when initializing a StraceParser object. Then the parse_trace method 
  of the parser can be called, which will return a list of Syscall objects, 
  each containing all the information about a single system call parsed 
  from the AST

"""

from .. import Syscall
from .Parser import Parser

import json

DEBUG = False


class ASTParser(Parser):
    """
    <Purpose>
    
    <Attributes>
      self.trace_path:
        The path to the file containing JSON with system calls

      self.syscall_definitions:
        A list of definitions describing each system calls

    """

    def __init__(self, trace_ast, *args, **kwargs):
        """
        <Purpose>
          Creates a ASTParser object  containing all the information needed to
          extract data from a trace file generated from this library as an AST.
        
        <Arguments>
          trace_path:
            The path to the trace file containing the traced system calls. This file
            should contain the output of an originally generated AST object.
          pickle_file:
            The path to the pickle file containing the parsed system call
            representations.

				<Side Effects>
          None
        
        <Returns>
          None
        """
        self.trace_ast = trace_ast
        super(ASTParser, self).__init__(*args, **kwargs)

    def _detect_trace_options(self):
        pass

    def _get_home_environment(self):
        pass

    def parse_trace(self):

        # finished system calls
        syscalls = []

        # prioritize trace_path if exists
        if self.trace_path != None:
            with open(self.trace_path) as handler:
                ast_obj = json.load(handler)
        else:
            ast_obj = self.trace_ast

        for syscall_ast in ast_obj:
            syscalls.append(Syscall.Syscall(self.syscall_definitions, None,
                                        syscall_ast, parse_mode=1))

        return syscalls
