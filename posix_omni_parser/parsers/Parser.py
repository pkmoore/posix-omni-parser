"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>
  Acts as the parent for all parsers. Defines some abstract methods required by
  all parsers and some helper methods that can be used by any parser.

"""

import pickle


class Parser():

    def __init__(self, trace_path, pickle_file):
        """
        <Purpose>
          Creates an Parser object which acts as the parent of parsers targeting
          specific interposition utilities.
        
        <Arguments>
          trace_path:
            The path to the trace file containing the traced system calls. This file
            should contain the output of the strace utility.
          pickle_file:
            The path to the pickle file containing the parsed system call 
            representations.

        <Side Effects>
          None
        
        <Returns>
          None
        """

        self.trace_path = trace_path

        # get the system call definitions from the pickle file. These will be used
        # to parse the parameters of each system call.
        self.syscall_definitions = pickle.load(open(pickle_file, 'rb'))

        # detect the options used in with the tracing utility. These options will be later used to
        # parse all the trace lines of the file.
        self.trace_options = self._detect_trace_options()

        # get the HOME environment variable. Normally the environment variable appears as arguments
        # of the execve system call. execve syscall should be the first system call in a trace. The
        # HOME environment variable is useful as general information about the trace and in
        # particular when a file bundle needs to be generated. To generate a file bundle all the
        # files referenced in the trace must be located and included in the bundle. The location of
        # these files is in respect to the HOME variable if one is found, otherwise the home
        # directory is assumed to be the current directory (pwd)
        self.home_env = self._get_home_environment()


    """ ABSTRACT METHODS """
    def _get_home_environment(self):
        raise NotImplementedError

    def _detect_trace_options(self):
        raise NotImplementedError

    def parse_trace(self):
        raise NotImplementedError


    def _merge_quote_args(self, args_list):
        """
        <Purpose>
          Used to fix errors on parsed arguments. Specifically, if a string value in
          the trace contains ", " the string will be wrongly split in two arguments.
          This method searches for arguments that start with a double quote and if
          that argument does not end with a double quote (an un-escaped double quote)
          then the argument must have been wrongly split into two. Reconstruct the
          original argument by joining the current part of the argument with the next
          part in the arguments list.
        
        <Arguments>
          args_list:
            A list of string arguments.
        
        <Exceptions>
          None
        
        <Side Effects>
          None
        
        <Returns>
          line_parts:
            The updated line_parts.
        
        """

        if len(args_list) <= 1:
            return args_list

        index = 0
        while index < len(args_list):
            # if the current argument starts with a quote but does not end with a quote,
            # then the argument must have been wrongly split.
            if args_list[index].startswith("\""):
                while index + 1 < len(args_list):
                    if self._ends_in_unescaped_quote(args_list[index].strip(".")):
                        break
                    args_list[index] += ", " + args_list[index + 1]
                    args_list.pop(index + 1)
            index += 1

        return args_list


    def _ends_in_unescaped_quote(self, string):
        """
        Helper method for _merge_quote_args
        """
        if not string or string[-1] != '"':
            return False

        for index in range(-2, -len(string) - 1, -1):
            if string[index] != '\\':
                return index % 2 == 0

        return False


