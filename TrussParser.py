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
    