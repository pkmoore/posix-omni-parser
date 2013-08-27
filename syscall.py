import parsing_classes

DEBUG = False




class UnfinishedSyscall:
  """
  If a syscall is interrupted or blocked, strace will split it in multiple 
  lines.
  
  Example:
  19176 accept(3, <unfinished ...>
  19175 connect(5, {sa_family=AF_INET, sin_port=htons(25588), 
                    sin_addr=inet_addr("127.0.0.1")}, 16) = 0
  19176 <... accept resumed> {sa_family=AF_INET, sin_port=htons(42572), 
                              sin_addr=inet_addr("127.0.0.1")}, [16]) = 4

  This object is used to store the information from the unfinished syscall until
  it is resumed.
  """
  
  def __init__(self, pid, name, args):
    self.pid = pid
    self.name = name
    self.args = args

  def __eq__(self, other):
    return self.pid == other.pid and self.name == other.name

  def __ne__(self, other):
    return not self.__eq__(other)
  
  def __repr__(self):
    return "UnfinishedSyscall: " + self.pid + \
           " " + self.name + " " + str(self.args)




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
