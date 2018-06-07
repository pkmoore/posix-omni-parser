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

from parsers.StraceParser import StraceParser
from parsers.TrussParser import TrussParser


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

    def __init__(self, trace_path=None):
        """
        <Purpose>
          Creates a trace object containing all the information extracted from a 
          trace file.
        
        <Arguments>
          trace_path:
            The path to the trace file containing all needed information.
        
        <Exceptions>
          IOError:
            If no trace_path is given.
          
          IOError:
            If the trace_path given is not a file.
        
        <Side Effects>
          None
        
        <Returns>
          None
        """

        self.trace_path = trace_path

        # Were we given a trace path?
        if self.trace_path == None:
            raise IOError("A trace file is needed to initialize a Trace object")

        # does this file exist?
        if not os.path.exists(self.trace_path):
            raise IOError("Could not find trace file `" + self.trace_path + "`")

        # detect tracing utility used to generate the trace file. peek here to avoid
        # re-initializing the file.
        self.tracing_utility = self._detect_tracing_utility()

        # select parser according to the tracing utility.
        if self.tracing_utility == "strace":
            self.parser = StraceParser(self.trace_path)
        elif self.tracing_utility == "truss":
            self.parser = TrussParser(self.trace_path)
        else:
            raise Exception("Unknown parser when attempting to parse trace.")

        # parse system calls
        self.syscalls = self.parser.parse_trace()

        # get platform information
        self.platform = sys.platform

        # - in bundle can store metadata what command / date / OS / etc the trace was
        # - gathered from.


    def _detect_tracing_utility(self):
        """
        <Purpose>
          Using the trace file given in self.trace_path figure out which tracing 
          utility was used to generate this trace file.
        
        <Arguments>
          None
        
        <Exceptions>
          None
        
        <Side Effects>
          None
        
        <Returns>
          tracing_utility:
            The name of the tracing utility used to generate the trace file.
        """

        # TODO: Unimplemented. return strace for now
        tracing_utility = "strace"

        return tracing_utility

    def __repr__(self):
        representation = "<Trace\nplatform=" + self.platform \
                       + "\ntrace_path=" + self.trace_path \
                       + "\ntracing_utility=" + self.tracing_utility \
                       + "\nparser=" + str(self.parser) \
                       + "\ntraced_syscalls=" + str(len(self.syscalls)) + ">"

        return representation

"""
    def generate_trace_bundle(self):
        " ""
        <Purpose>
          Generates the Lind File System.
          a. Find all file paths involved in the system calls parsed in the previous step.
          b. Based on the system call outcome decide whether the files referenced by these file 
              paths existed in the POSIX fs at the time the trace file was generated.
          c. If it did, generate that file in the Lind fs, ignore otherwise.
          d. Any previous Lind fs files are removed and overridden.
        
          Generates a trace bundle.
          a. Serializes and stores the parsed trace actions.
          b. Generates a tarfile containing the original trace file, the serialized 
             parsed trace file and the Lind fs data and metadata files.
          c. Removes original trace file, serialized file and Lind fs files.
        
        <Arguments>
          None
        
        <Exceptions>
          None
        
        <Side Effects>
          None
        
        <Returns>
          None
        
        " ""

        # generate the initial file system needed by the model. This will create a
        # set of files that make up the file system containing all the files
        # referenced in the trace
        generate_fs.generate_fs(self.syscalls, self.trace_path)

        # pickle the trace
        pickle_name = "actions.pickle"
        pickle_file = open(pickle_name, 'w')
        cPickle.dump(actions, pickle_file)
        pickle_file.close()

        # Now we have everything we need, create the trace bundle which will include
        # the trace pickle and the lind fs files.

        # first find a name for the bundle archive.
        head, bundle_name = os.path.split(trace_path)

        # if the bundle_name already exists, append a number.
        temp_count = ''
        bundle_extension = ".trace_bundle"
        while os.path.exists(bundle_name + temp_count + bundle_extension):
          if temp_count == '':
            temp_count = '1'
          else:
            temp_count = str(int(temp_count) + 1)
        bundle_name += temp_count + bundle_extension

        # Create the bundle archive.
        tar = tarfile.open(bundle_name, "w")

        # add the original trace file.
        original_trace_name = "original_trace." + parser
        # let's copy it locally and rename it first.
        shutil.copyfile(trace_path, original_trace_name)
        tar.add(original_trace_name)

        # add the pickle file
        tar.add(pickle_name)

        # add the lind fs metadata file
        if not os.path.exists("lind.metadata"):
          raise Exception("Lind fs metadata file not found.")
        tar.add("lind.metadata")

        # add the lind fs data files
        for fname in os.listdir(os.getcwd()):
          if fname.startswith("linddata."):
            tar.add(fname)

        tar.close()

        # Finally, clean up all intermediate files
        os.remove(original_trace_name)
        os.remove(pickle_name)
        os.remove("lind.metadata")
        for fname in os.listdir(os.getcwd()):
          if fname.startswith("linddata."):
            os.remove(fname)

"""



def main():
    trace = Trace(sys.argv[1])
    print trace

    print

    for syscall in trace.syscalls:
        print syscall

if __name__ == "__main__":
    main()
