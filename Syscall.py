import POT_parsing_classes

DEBUG = True

class Syscall:
  """
  """

  def __init__(self, parser, line, line_parts):
    """
    <parameters>
      line_parts[] - a list containing the parts of the parsed trace line.
        (type, pid, name, args, return, inst_pointer, timestamp, elapsed_time)
    """

    self.parser = parser
    self.original_line = line

    self.type = line_parts["type"]
    self.pid = line_parts["pid"]
    self.name = line_parts["name"]

    # at these point all system call arguments are represented as strings. Let's
    # cast them into more meaningful classes.
    self.args = POT_parsing_classes.cast_args(self.name, 
                                              self.parser.syscall_definitions, 
                                              line_parts["args"])

    self.ret = line_parts["return"]
    self.inst_pointer = line_parts["inst_pointer"]
    self.timestamp = line_parts["timestamp"]
    self.elapsed_time = line_parts["elapsed_time"]


  def __repr__(self):
    """
    """

    representation = "original line: " + self.original_line + "\n" \
                   + "type: " + self.type + "\n" \
                   + "pid: " + str(self.pid) + "\n" \
                   + "name: " + self.name  + "\n" \
                   + "args: " + str(self.args) + "\n" \
                   + "return: " + str(self.ret) + "\n" \
    
    if self.inst_pointer:
      representation += "inst_pointer: " + self.inst_pointer + "\n" \

    if self.timestamp:
      representation += "timestamp: " + str(self.timestamp) + "\n" \
    
    if self.elapsed_time:
      representation += "elapsed_time: " + str(self.elapsed_time) + "\n"

    return representation


