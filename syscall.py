import parsing_classes

DEBUG = False

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
    self.args = parsing_classes.cast_args(self.name, line_parts["type"],
                                          self.parser.syscall_definitions, 
                                          line_parts["args"])

    self.ret = line_parts["return"]
    self.inst_pointer = line_parts["inst_pointer"]
    self.timestamp = line_parts["timestamp"]
    self.elapsed_time = line_parts["elapsed_time"]


  def __repr__(self):
    """
    """

    representation = "ORIGINAL LINE: " + self.original_line + "\n" \
                   + "TYPE: " + self.type + "\n" \
                   + "PID: " + str(self.pid) + "\n" \
                   + "NAME: " + self.name  + "\n" \
                   + "ARGS: " + str(self.args) + "\n" \
                   + "RETURN: " + str(self.ret) + "\n" \
    
    if self.inst_pointer:
      representation += "INST_POINTER: " + self.inst_pointer + "\n" \

    if self.timestamp:
      representation += "TIMESTAMP: " + str(self.timestamp) + "\n" \
    
    if self.elapsed_time:
      representation += "ELAPSED_TIME: " + str(self.elapsed_time) + "\n"

    return representation
