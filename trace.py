# TODO:
# - detectTracingUtility
#
#
###############################################

"""

"""
import os
import sys
import pickle

import strace_parser


class Trace:
  """
  This object represents an entire trace, that is all the information about a 
  trace file created from an interposition utility like strace, truss and 
  dtrace.
  """

  def __init__(self, trace_path=None):
    """
    <parameters>

    """

    self.trace_path = trace_path

    # Were we given a trace path?
    if self.trace_path == None:
      raise Exception("A trace file is needed to initialize a Trace object")

    # does this file exist?
    if not os.path.exists(self.trace_path):
      raise Exception("Could not find trace file `" + self.trace_path + "`")

    # detect tracing utility used to generate the trace file.
    # peek here to avoid re-initializing the file.
    self.tracing_utility = self._detect_tracing_utility(trace_path)

    # get the syscall definitions from the pickle file. These  will be used to
    # parse the parameters of each system call.
    syscall_definitions = None
    try:
      pickle_file = open("syscall_definitions.pickle", 'rb')
      syscall_definitions = pickle.load(pickle_file)
    finally:
      pickle_file.close()

    # select parser according to the tracing utility.
    if self.tracing_utility == "strace":
      self.parser = strace_parser.StraceParser(trace_path, syscall_definitions)
    elif self.tracing_utility == "truss":
      # not yet implemented.
      self.parser = TrussParser(trace_path, syscall_definitions)
    else:
      raise Exception("Unknown parser when attempting to parse trace.")

    # parse system calls
    self.syscalls = self.parser.parse_trace()

    # get platform information
    self.platform = sys.platform
    
    #- in bundle can store metadata what command / date / OS / etc the trace was
    #- gathered from.


  def _detect_tracing_utility(self, trace_path):
    """
    <parameters>

    """

    tracing_utility = "strace"

    assert tracing_utility in ["strace", "truss"]
    return tracing_utility

  
  def generate_trace_bundle(trace_path, parser=None):
    """
    Given a path to a trace file, this function performs the following operations:
    A. Parses the system calls from the trace file.
    B. Generates the Lind File System.
        a. Find all file paths involved in the system calls parsed in the previous 
           step.
        b. Based on the system call outcome decide whether the files referenced by 
           these file paths existed in the POSIX fs at the time the trace file was 
           generated.
        c. If it did, generate that file in the Lind fs, ignore otherwise.
        d. Any previous Lind fs files are removed and overridden.
    C. Generates a trace bundle.
        a. Serializes and stores the parsed trace actions.
        b. Generates a tarfile containing the original trace file, the serialized 
           parsed trace file and the Lind fs data and metadata files.
        c. Removes original trace file, serialized file and Lind fs files.
    """

    # generate the initial file system needed by the model.
    generate_lind_fs.generate_fs(actions, trace_path)
    
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
    representation = "<Trace \nplatform=" + self.platform \
                   + "\ntrace_path=" + self.trace_path \
                   + "\ntracing_utility=" + self.tracing_utility \
                   + "\nself.parser=" + str(self.parser) \
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