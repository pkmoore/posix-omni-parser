"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>

"""

import Parser
import Syscall

DEBUG = False


class TrussParser(Parser.Parser):
  """
  <Purpose>

  <Attributes>
  """


  def __init__(self, trace_path):
    """
    <Purpose>

    <Arguments>
      trace_path:
        The path to the trace file containing the traced system calls. This file
        should contain the output of the truss utility.

    <Exceptions>
      IOError:
        If the pickle file containing the system call definitions is not found.
        (this file should come as part of this program)
    
    <Side Effects>
      None

    <Returns>
      None
    """

    super(TrussParser, self).__init__(trace_path)
  



  def _detect_trace_options(self):
    """
    <Purpose>


      Truss options (taken from truss man page):

      -a  Shows the argument strings that are passed in each exec() system call.
      
      -e  Shows the environment strings that are passed in each exec() system 
          call.
      
      -d  Includes a time stamp on each line of trace output (seconds.fraction)
          relative to the beginning of the trace. The first line of the trace
          output shows the base time from which the individual time stamps are
          measured, both as seconds since the epoch and as a date string.
      
      -D  Includes a time delta on each line, represents the elapsed time for
          the LWP that incurred the event since the last reported event incurred
          by that LWP. Specifically, for system calls, this is not the time
          spent within the system call.

      -E  Includes a time delta on each line of trace output. The value appears
          as a field containing seconds.fraction and represents the difference
          in time elapsed between the beginning and end of a system call. In
          contrast to the -D option, this is the amount of time spent within the
          system call.

      -f  Follows all children created by fork() or vfork().

      -l  Includes the id of the responsible lightweight process (LWP) with each
          line of trace output. If -f is also specified, both the process-id and
          the LWP-id are included.

      -o  File to be used for the trace output. By default, the output goes to 
          standard error.

      -r  Shows the full contents of the I/O buffer for each read() on any of
          the specified file descriptors. The output is formatted 32 bytes per
          line and shows each byte as an ASCII character (preceded by one blank)
          or as a 2-character C language escape sequence for control characters
          such as horizontal tab (\t) and newline (\n). If ASCII
          interpretation is not possible, the byte is shown in 2-character
          hexadecimal representation. (The first 12 bytes of the I/O buffer for
          each traced print >read() are shown even in the absence of -r.)
          Default is -r!all.


      -v  Verbose. Displays the contents of any structures passed by address to
          the specified system calls (if traced by -t). Input values as well as
          values returned by the operating system are shown. For any field used
          as both input and output, only the output value is shown. Default is
          -v!all.

      -w  Shows the contents of the I/O buffer for each write() on any of the
          specified file descriptors (see the -r option). Default is -w!all.



    <Arguments>
      None

    <Exceptions>
      None
    
    <Side Effects>
      None

    <Returns>
      
    """