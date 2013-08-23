"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>
  This module contains the Trace object, which is used to capture all the
  extracted information from a trace file.

  Example using this module:

    import trace
    trace = trace.Trace(path_to_trace)
    print(trace)

"""

import os
import sys
import pickle

import strace_parser


class Trace:
  """
  <Purpose>
    This object represents an entire system call trace, which means taht it 
    holds all the information extracted from a system call trace file created by
    an interposition utility such as the strace utility on Linux, the truss 
    utility on Solaris or the dtrace utility on BSD and OSX platforms.

  <Attributes>
    self.trace_path:
      The path to the file containing the traced system calls.
    
    self.tracing_utility:
      The detected tracing utility used to generate the trace file, e.g strace.
    
    self.home_env:
      This instance variable holds the contents of the HOME environment 
      variable, if this information can be extracted from the trace file itself.

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
      
      IOError:
        If the pickle file containing the system call definitions (this file 
        comes as part of the program) is not found.
    
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

    # detect tracing utility used to generate the trace file.
    # peek here to avoid re-initializing the file.
    self.tracing_utility = self._detect_tracing_utility()

    # get the HOME environment variable. Normally environment variables appear
    # as arguments of the execve system call. execve syscall should be the first
    # system call in a trace. The HOME environment variable is useful as general
    # information about the trace but also in case a file bundle needs to be
    # generated. In this case all the files referenced in the trace must be
    # located and included in the bundle. The location of these files are in
    # respect to the HOME variable.
    self.home_env = self._get_home_environment()

    # get the syscall definitions from the pickle file. These  will be used to
    # parse the parameters of each system call.
    syscall_definitions = None
    try:
      pickle_file = open("syscall_definitions.pickle", 'rb')
      syscall_definitions = pickle.load(pickle_file)
    except IOError:
      raise IOError("The pickle file holding the system call definitions " + 
                    "was not found. (syscall_definitions.pickle)")
    finally:
      pickle_file.close()

    # select parser according to the tracing utility.
    if self.tracing_utility == "strace":
      self.parser = strace_parser.StraceParser(self.trace_path, syscall_definitions)
    elif self.tracing_utility == "truss":
      # not yet implemented.
      self.parser = TrussParser(self.trace_path, syscall_definitions)
    else:
      raise Exception("Unknown parser when attempting to parse trace.")

    # parse system calls
    self.syscalls = self.parser.parse_trace()

    # get platform information
    self.platform = sys.platform
    
    #- in bundle can store metadata what command / date / OS / etc the trace was
    #- gathered from.


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

    tracing_utility = "strace"

    return tracing_utility

  
  def _get_home_environment(self):
    """
    <Purpose>
      Read the first line of the trace file. If that line represents the execve
      system call then examine it to see whether the HOME environment variable
      is set. If it is set, extract it and return it, otherwise return None. The
      HOME environment variable is sometimes set to a path other than the
      current directory (i.e the directory in which the traced application was
      executed) when running a benchmark. Keeping track of the HOME env variable
      is particularly useful when reasoning about relative paths that appear in
      the trace file. System calls referring to files using relative paths,
      might refer to these files relative to the HOME variable defined in the
      execve syscall.

    <Arguments>
      None

    <Exceptions>
      IOError:
        Unable to read from the trace file.
    
    <Side Effects>
      None

    <Returns>
      The HOME env path as this is defined in the execve system call, or None if
      the HOME path was not found.

    """
    
    try:
      fh = open(self.trace_path, "r")
      # the execve syscall is the first action of the trace file
      execve_line = fh.readline()
    except IOError:
      raise IOError("Unable to read trace file when trying to extract the " + 
                    "HOME environment variable.")
    finally:
      fh.close()
    
    # If the 'HOME' variable is defined in the execve line, the HOME_PATH
    # variable will be set to the path of 'HOME'.
    if "execve(" in execve_line:
      # split to get the arguments of the syscall
      execve_parts = execve_line.split(", ")

      # the parameter of the HOME variable in the execve syscall has this
      # format: 
      # "HOME=/home/savvas/tests/" including the double quotes.
      for part in execve_parts:
        if part.startswith("\"HOME="):
          # remove the double quotes
          part = part.strip("\"")
          
          # return the path excluding the "HOME="" label in front of it.
          return part[part.find("HOME=")+5:]

    return None

 
  def generate_trace_bundle(self):
    """
    <Purpose>
      Generates the Lind File System.
      a. Find all file paths involved in the system calls parsed in the previous 
         step.
      b. Based on the system call outcome decide whether the files referenced by 
         these file paths existed in the POSIX fs at the time the trace file was 
         generated.
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

    """

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


  def __repr__(self):
    representation = "<Trace\nplatform=" + self.platform \
                   + "\ntrace_path=" + self.trace_path \
                   + "\ntracing_utility=" + self.tracing_utility \
                   + "\nparser=" + str(self.parser) \
                   + "\nhome_env=" + str(self.home_env) \
                   + "\ntraced_syscalls=" + str(len(self.syscalls)) + ">"

    return representation






def main():
  trace = Trace(sys.argv[1])
  print(trace)

  print()

  for syscall in trace.syscalls:
    print(syscall)

if __name__ == "__main__":
  main()