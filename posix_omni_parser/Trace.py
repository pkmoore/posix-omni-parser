"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>
  This module contains the Trace object, which is used to capture all the
  extracted information from a trace file.

  Example using this module:

    import Trace
    trace = Trace.Trace(path_to_trace)
    print trace

"""

import os
import sys
import json

import Syscall
from parsers.StraceParser import StraceParser
from parsers.ASTParser import ASTParser

class Trace:
    """
    <Purpose>
      This object represents an entire system call trace, which means that it 
      holds all the information extracted from a system call trace file created by
      an interposition utility such as the strace utility on Linux, the truss 
      utility on Solaris or the dtrace utility on BSD and OSX platforms.
    
    <Attributes>
      self.trace_path:
        The path to the file containing the traced system calls.
      
      self.tracing_utility:
        The detected tracing utility used to generate the trace file, e.g strace.
      
      self.parser:
        The parser to use in order to extract the information from the trace file.
        The choice of parser depends on the tracing utility used to generate the 
        trace file, i.e self.tracing_utility.
    
      self.syscalls:
        This variable holds all the parsed system calls. It is a list of Syscall
        objects returned by the parser.
    
      self.platform:
        The platform in which the trace is parsed on (sys.platform). This is
        especially useful when creating a trace bundle containing not only the
        parsed system calls but also a representation of all the files referenced
        in trace file.
    """

    def __init__(self, trace_path, pickle_file):
        """
        <Purpose>
          Creates a trace object containing all the information extracted from a 
          trace file.
        
        <Arguments>
          trace_path:
            The path to the trace file containing all needed information.
          pickle_file:
            The path to the pickle file containing the parsed system call
            representations.
        
        <Exceptions>
          IOError:
            If no trace_path or pickle_file is given
          
          IOError:
            If the trace_path or pickle_file given is not a file
        
        <Side Effects>
          None
        
        <Returns>
          None
        """

        self.trace_path = trace_path
        self.pickle_file = pickle_file

        # Were we given a trace path?
        if self.trace_path == None:
            raise IOError("A trace file is needed to initialize a Trace object")

				# Were we given a pickle file path?
        if self.pickle_file == None:
            raise IOError("A pickle file is needed to initialize a Trace object")

        # do these file exist?
        if not os.path.exists(self.trace_path):
						raise IOError("Could not find trace file `" + self.trace_path + "`")
        if not os.path.exists(self.pickle_file):
            raise IOError("Could not find pickle file `" + self.pickle_file + "`")

        # detect tracing utility used to generate the trace file. peek here to avoid
        # re-initializing the file.
        self.tracing_utility = "strace"

        # set strace parser
        self.parser = StraceParser(self.trace_path, self.pickle_file)

        # parse system calls
        self.syscalls = self.parser.parse_trace()

        # get platform information
        self.platform = sys.platform

        # - in bundle can store metadata what command / date / OS / etc the trace was
        # - gathered from.


    def to_ast(self):
        """
        <Purpose>
          CRASHSIMULATOR MODIFIED

          Generate a JSON-ready AST of the trace in order for
          better anomaly injection. For each system call, store the
          PID, name, arguments and return value in a dict, and append to
          a parse tree list.

        <Returns>
          None

        """

        parse_tree = []

        for syscall in self.syscalls:
            ast = {
              'type': syscall.type,
              'pid': syscall.pid,
              'name': syscall.name,
              'args': [
                  arg.to_ast(num) for num, arg in enumerate(syscall.args)
              ],
              'return': syscall.ret[0]
            }
            parse_tree.append(ast)

        # return the parse tree with all system calls
        return parse_tree


    def from_ast(self, trace_ast):
      """
      <Purpose>
        CRASHSIMULATOR MODIFIED

        From a (mutated) AST, reimport into the trace object, replacing
        self.syscalls with the altered changes. From here, execution from
        CrashSimulator context can continue.

      <Returns>
        None

      """

      # store the original syscalls elsewhere and delete it.
      self.orig_syscalls = self.syscalls
      del self.syscalls

      # reinitialize the parser as an ASTParser
      self.parser = ASTParser(trace_ast, None, self.pickle_file)

      # load the AST object back into a posix-omni-parser object
      self.syscalls = self.parser.parse_trace()


    def __repr__(self):
        representation = "<Trace\nplatform=" + self.platform \
                       + "\ntrace_path=" + self.trace_path \
                       + "\ntracing_utility=" + self.tracing_utility \
                       + "\nparser=" + str(self.parser) \
                       + "\ntraced_syscalls=" + str(len(self.syscalls)) + ">"

        return representation
