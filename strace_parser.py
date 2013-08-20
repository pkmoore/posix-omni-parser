import re
import pickle

import syscall

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



class StraceParser:
  """
  """

  def __init__(self, trace_path, syscall_definitions):
    """
    """
    self.trace_path = trace_path
    self.syscall_definitions = syscall_definitions
    
    # detect the options used in with the tracing utility. These options will be
    # later used to parse all the trace lines of the file.
    self.trace_options = self._detect_trace_options()

    # regex compiled for _parse_line
    #
    # Example unfinished syscall.
    # accept(3,  <unfinished ...>
    #
    # Example complete syscall.
    # socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 5 <0.000066>
    #
    # Example resumed syscall.
    # <... accept resumed> {sa_family=AF_INET, sin_port=htons(44289), sin_addr=inet_addr("127.0.0.1")}, [16]) = 4 <0.002020>
    #
    # Example unfinished syscall due to end of program.
    # nanosleep({...},  <unfinished ... exit status 0>
    self._re_unfinished_syscall = re.compile(r"([^(]+)\((.*)\<unfinished .*")
    self._re_resumed_syscall = re.compile(r"\<\.\.\. ([^ ]+) resumed\> (.*)\)[ ]+=[ ]+([a-fx\d\-?]+)(.*)")
    self._re_complete_syscall = re.compile(r"([^(]+)\((.*)\)[ ]+=[ ]+([a-fx\d\-?]+)(.*)")
    


  def _detect_trace_options(self):
    """
    "inst_pointer" True/False -i
    "timestamp" None/"r"/"t"/"tt"/"ttt"
    "elapsed_time" True/False -T
    "verbose" True/False -v
    "output" True/False -o
    "fork" True/False -f
    """

    # read the first line of the trace to detect the used options.
    with open(self.trace_path) as trace_file_handler:
      trace_line = trace_file_handler.readline()

    # check if the general format of a trace line is correct.
    # example: 8085  open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    if (trace_line.find('(') == -1 or trace_line.find(')') == -1 
     or trace_line.find('=') == -1):
      raise Exception("Incorrect format of trace line `" + trace_line + "`")


    """
    The strace parser allows for any combination of a set of options when using 
    strace to gather traces. Some of these options are required and others are 
    optional.

    Handled options (from strace man page). (R) indicates a required option.
    -i     Print the instruction pointer at the time of the system call.
    -r     Print a relative timestamp upon entry to each system call.  This 
           records the time difference between the beginning of successive 
           system calls.
    -t     Prefix each line of the trace with the time of day.
    -tt    If given twice, the time printed will include the microseconds.
    -ttt   If given thrice, the time printed will include the microseconds and 
           the leading portion will be printed as the number of seconds since 
           the epoch.
    -T     Show the time spent in system calls. This records the time difference 
           between the beginning and the end of each system call.
    -v (R) Print unabbreviated versions of environment, stat, termios etc calls.
           These structures are very common in calls and so the default behavior 
           displays a reasonable subset of structure members. Use this option to 
           get all of the gory details.
    -o (R) Write the trace output to a file rather than to stderr.
    -f (R) Trace child processes as they are created by currently traced 
           processes as a line_parts of the fork(2) system call.
    
    Note: The parser requires each traced system call to include the process id.
          This is achieved by using both the -f and -o options.

    Example strace output with different options. Required options -v -f and -o 
    are included in each of the following examples.

    with no extra options:
      8085  open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -i:
      8088  [b7739424] open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -r:
      8091  0.000539 open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -t:
      8094  15:31:56 open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -tt:
      8097  15:32:16.190216 open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -ttt:
      8100  1371472360.671434 open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
    -T:
      8106  open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3 <0.000040>

    An example with all handled options: strace -irtttTvfo output_file command
      8112  0.000587 [b7795424] open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3 <0.000037>
    
    Note here how the -r option overrides the -ttt (or -t or -tt) option. In 
    other words the two following executions of strace have the exact same 
    outcome:
      strace -irtttTvfo output_file command
      strace -irTvfo output_file command

    To get time stats skip the -r option: strace -itttTvfo output_file command
      8168  1371473138.416217 [b7782424] open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3 <0.000037>
    """

    # content differences based on the strace options we care about appear in
    # three different parts of the trace line. The first one is before the name
    # of the system call, the second part is witin the parameter set of the
    # system call and the last one is after the return part of the system call,
    # as shown in the examples above.
    m = re.match(r"(.+)\((.+)\)[ ]+=[ ]+[-0-9]+(.*)", trace_line)
    if m:
      upto_first_bracket_string = m.group(1)
      parameters_string = m.group(2)
      after_return_string = m.group(3)
    else:
      raise Exception("Invalid format when parsing parts of trace line `"
                      + trace_line + "`")

    # let's first check for options -o -f -i, -r, -t, -tt and -ttt which impose
    # changes before the name of the system call.
    front_parts = upto_first_bracket_string.split()

    # front_parts should include the name of the syscall, the pid and optionally
    # other information based on options used with the strace utility.
    if len(front_parts) < 1 or len(front_parts) > 4:
      # if the string before the first openning bracket has less than 1 parts or
      # more than 4 parts, the format of the trace line is incorrect.
      raise Exception("Invalid format of front part of trace line `" \
                      + trace_line + "`")
    elif len(front_parts) == 1:
      # if there is only one part, it must be the name of the system call in
      # which case the pid is not included. So the required -f option must have
      # not been used.
      raise Exception("Required option -f not used in trace line `"
                      + trace_line + "`")

    # remove the name of the system call from the list. Syscall name is always
    # last in the list. We will need the system call name later.
    syscall_name = front_parts.pop()

    # remove the pid from the list. pid is always first in the list.
    pid = front_parts.pop(0)

    # pid should be an integer
    assert pid.isdigit(), "Invalid format of pid in trace line `" + trace_line + "`"

    # Since the pid exists, the -o and -f options must have been set.
    trace_options = {}
    trace_options["output"] = True
    trace_options["fork"] = True

    # front_parts should now have a maximum of 2 values representing options
    # [-t or -tt or -ttt or -r] and -i
    trace_options["timestamp"] = None
    trace_options["inst_pointer"] = False
    
    if len(front_parts) > 0:
      # check if the first value of front_parts corresponds to the -i option, eg
      # [b7782424]
      if "[" in front_parts[0] and "]" in front_parts[0]:
        trace_options["inst_pointer"] = True
        front_parts.pop(0)
      else:
        # if it's not a value of the -i option it must be one of the -t, -tt,
        # -ttt or -r options.
        if ":" in front_parts[0]:
          # if the value contains a ":" it must be either a -t or a -tt
          if "." in front_parts[0]:
            trace_options["timestamp"] = "tt"
          else:
            trace_options["timestamp"] = "t"
        else:
          # if the value does not contain a ":" it must be a -r or a -ttt
          assert "." in front_parts[0], "Invalid value `" + front_parts[0] + "` when parsing option -r or -ttt"

          # get the number of seconds from the value.
          seconds = int(front_parts[0][:front_parts[0].find(".")])
          
          # seconds since epoch when writting this.
          epoch_seconds = 1371488434
          
          if seconds > epoch_seconds:
            trace_options["timestamp"] = "ttt"
          else:
            trace_options["timestamp"] = "r"

        front_parts.pop(0)

        if len(front_parts) > 0:
          assert "[" in front_parts[0] and "]" in front_parts[0], "Invalid format when trying to parse value of -i option"
          trace_options["inst_pointer"] = True
          front_parts.pop(0)

    # all option values were consumed so there should be no more parts left.
    assert len(front_parts) == 0, "Invalid options found when parrsing options" + str(front_parts)

    """
    Now let's check if the required option -v was used. We can figure this out 
    by examining the parameters of the trace line. The trace line must represent
    the execve system call, otherwise the parameter set will not indicate 
    whether -v option was set. This should always be the case since the first
    line of the trace file should be the execve syscall.

    Example strace outcomes of the execve system call which should always be the
    first system call traced. The first example shows the strace outcome when
    not using the -v option which is unaccepted. The second example shows the
    strace outcome when using the -v option.

    Example without the -v option:
    8313  execve("./syscalls", ["./syscalls", "open"], [/* 39 vars */]) = 0

    Example with -v option:
    8302  execve("./syscalls", ["./syscalls", "open"], ["SSH_AGENT_PID=23702",
    "GPG_AGENT_INFO=/tmp/keyring-yZgM"..., "TERM=xterm", "SHELL=/bin/bash",
    "XDG_SESSION_COOKIE=f7e455fdc4915"..., "WINDOWID=73407903",
    "GNOME_KEYRING_CONTROL=/tmp/keyri"..., "USER=savvas",
    "LS_COLORS=rs=0:di=01;34:ln=01;36"...,
    "XDG_SESSION_PATH=/org/freedeskto"...,
    "XDG_SEAT_PATH=/org/freedesktop/D"..., "SSH_AUTH_SOCK=/tmp/keyring-
    yZgMt"..., "SESSION_MANAGER=local/savvas-not"...,
    "DEFAULTS_PATH=/usr/share/gconf/u"..., "XDG_CONFIG_DIRS=/etc/xdg/xdg-
    ubu"..., "GPGKEY=D61510C1", "PATH=/usr/lib/lightdm/lightdm:/u"...,
    "DESKTOP_SESSION=ubuntu", "PWD=/home/savvas/Desktop/CHECKAP"...,
    "GNOME_KEYRING_PID=23652", "LANG=en_US.UTF-8",
    "MANDATORY_PATH=/usr/share/gconf/"..., "UBUNTU_MENUPROXY=libappmenu.so",
    "COMPIZ_CONFIG_PROFILE=ubuntu", "GDMSESSION=ubuntu", "SHLVL=1",
    "HOME=/home/savvas", "GNOME_DESKTOP_SESSION_ID=this-is"...,
    "LOGNAME=savvas", "XDG_DATA_DIRS=/usr/share/ubuntu:"...,
    "DBUS_SESSION_BUS_ADDRESS=unix:ab"..., "LESSOPEN=| /usr/bin/lesspipe %s",
    "DISPLAY=:1", "XDG_CURRENT_DESKTOP=Unity", "LESSCLOSE=/usr/bin/lesspipe %s
    %"..., "COLORTERM=gnome-terminal", "XAUTHORITY=/home/savvas/.Xauthor"...,
    "OLDPWD=/home/savvas", "_=/usr/bin/strace"]) = 0
    
    The second example shows how when using the -v options, structure values are
    not abreviated, which is what we want.
    """

    # Let's make sure that the system call we are examining is execve.
    assert syscall_name == "execve", "Trace line does not include an execve system call `" + syscall_name + "`"

    # now if the parameters_string includes the strings "[/*" and "*/]" then the
    # -v option was not used.
    if "[/*" in parameters_string and "*/]" in parameters_string:
      raise Exception("Required option -v not used in trace line `" + trace_line + "`")

    # otherwise the -v option is there and we can continue.
    trace_options["verbose"] = True

    # finally let's check if the -T option was set. We can do this by checking
    # whether the string after the return part of the system call includes the
    # characters "<" and ">"
    trace_options["elapsed_time"] = False
    if "<" in after_return_string and ">" in after_return_string:
      trace_options["elapsed_time"] = True

    return trace_options



  def parse_trace(self):
    """
    """

    # this list will hold all the parsed system calls.
    syscalls = []

    # this list will hold all pending (i.e unfinished) syscalls
    unfinished_syscalls = []

    # open the trace file.
    trace_file_handler = open(self.trace_path)

    # process each line of the trace.
    for line in trace_file_handler:
      line = line.strip()

      # skip empty lines
      if line == '':
        continue

      if DEBUG:
        print(line)

      line_parts = self._parse_line(line, unfinished_syscalls)

      if line_parts != None:
        syscalls.append(syscall.Syscall(self, line, line_parts))

    trace_file_handler.close()

    return syscalls


  
  def _parse_line(self, line, unfinished_syscalls):
    """
    <return>
      line_parts:
        A dictionaly with:
        type:         Type of system call ("completed", "unfinished", "resumed")
        pid:          The process id (eg 8094)
        timestamp:    Start time of the syscall.
        inst_pointer: The instruction pointer at the time of the system call.
        name:         The name of the system call (eg "sendto")
        args:         A list of strings each representing a syscall arguments.
        return:       A list of two items. First item is +/- int or a hex number
                      or a '?' for syscalls that do not return (e.g. _exit 
                      syscall). The second item is either None or the error 
                      descriptor (string) or a list of returned values.
        elapsed_time: Time spent in syscall.

      None if the line passed is not a valid trace line.


      Notes:
      - timestamp, inst_pointer and elapsed_time are optional and exist only
        if the corresponding option is given. If the option is not given, the
        value is set to None.
      - Format and meaning of timestamp value depends on the timestamp option 
        (r/t/tt/ttt).
      - For unfinished syscalls (type="unfinished"), args is an incomplete set 
        of arguments. In addition, return and elapsed_time are always set to 
        None.
      - For syscalls that don't return, elapsed_time is set to None even if
        the corresponding option is given.
    """

    line_parts = {}

    remaining_line = line

    # pid is the first part of the line. 
    line_parts["pid"], remaining_line = remaining_line.split(None, 1)
    assert line_parts["pid"].isdigit(), "Invalid format of parsed pid in line `" + line + "`"

    # Ignore lines that indicate signals. These lines start with either "+++"
    # or "---" (after the pid)
    # Example:
    # 14037 --- SIGCHLD (Child exited) @ 0 (0) ---
    if remaining_line[:3] in ['+++', '---']:
      return None

    # if the timestamp option is set, the next part of the line will be the
    # timestamp.
    line_parts["timestamp"] = None
    if self.trace_options["timestamp"]:
      line_parts["timestamp"], remaining_line = remaining_line.split(None, 1)
      
    # if the inst_pointer option is set, the next part of the line will be the
    # inst_pointer.
    line_parts["inst_pointer"] = None
    if self.trace_options["inst_pointer"]:
      line_parts["inst_pointer"], remaining_line = remaining_line.split(None, 1)
      line_parts["inst_pointer"] = line_parts["inst_pointer"].strip("[]")

    # next, let's parse the name, args and return part of the line, according to
    # the type of the syscall.

    # Example unfinished syscall.
    # 15900 1371634358.110699 [b76e8424] accept(3,  <unfinished ...>
    # 14039 open("/dev/null", O_WRONLY <unfinished ...>
    
    # Example complete syscall.
    # 15899 1371634358.112335 [b76e8424] socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 5 <0.000066>
    
    # Example resumed syscall.
    # 15900 1371634358.112746 [b76e8424] <... accept resumed> {sa_family=AF_INET, sin_port=htons(44289), sin_addr=inet_addr("127.0.0.1")}, [16]) = 4 <0.002020>
    
    # Example non-returning syscall.
    # 15899 1371634358.112817 [b76e8424] exit_group(0) = ?

    # Example unfinished syscall due to end of program.
    # 15900 1371634358.112850 [????????] nanosleep({...},  <unfinished ... exit status 0>

    if "<unfinished ..." in remaining_line:
      line_parts["type"] = "unfinished"
      
      m = self._re_unfinished_syscall.match(remaining_line)
      if not m:
        raise Exception("Invalid format when parsing unfinished trace line `"
                        + line + "`")
      
      line_parts["name"] = m.group(1)
      line_parts["args"] = self._parse_args(m.group(2))
      line_parts["return"] = None
      
      # save unfinished syscall so that it can be reconstructed when resumed.
      unfinished_syscalls.append(UnfinishedSyscall(line_parts["pid"], 
                                                    line_parts["name"], 
                                                    line_parts["args"]))

      remaining_line = ''
    
    elif " resumed>" in remaining_line:
      line_parts["type"] = "resumed"
      
      m = self._re_resumed_syscall.match(remaining_line)
      if not m:
        raise Exception("Invalid format when parsing resumed trace line `"
                        + line + "`")

      line_parts["name"] = m.group(1)

      # there should be a saved unfinished syscall corresponding to this
      # resuming syscall. Let's find its index so we can pop it.
      unfinished_syscalls_index = None
      for index in range(0, len(unfinished_syscalls)):
        if (UnfinishedSyscall(line_parts["pid"], line_parts["name"], "")
                 ==  unfinished_syscalls[index]):
          unfinished_syscalls_index = index
          break

      # if the corresponding unfinished syscall was not found, something must
      # have gone wrong.
      if unfinished_syscalls_index == None:
        raise Exception("Unfinished syscall not found for resuming syscall `"
                        + line + "`")
      
      # merge the args of the unfinished syscall with this resuming syscall.
      line_parts["args"] = unfinished_syscalls.pop(unfinished_syscalls_index).args \
                            + self._parse_args(m.group(2))
      
      line_parts["return"] = m.group(3)
      remaining_line = m.group(4)

    else:
      line_parts["type"] = "completed"

      m = self._re_complete_syscall.match(remaining_line)
      if not m:
        raise Exception("Invalid format when parsing completed trace line `"
                        + line + "`")

      line_parts["name"] = m.group(1)
      line_parts["args"] = self._parse_args(m.group(2))
      line_parts["return"] = m.group(3)
      remaining_line = m.group(4)

    # if the type of the syscall is unfinished then there is nothing else to
    # parse.
    line_parts["elapsed_time"] = None
    if line_parts["type"] == "unfinished":
      return line_parts

    # at this point the remaining line should include the error label eg ENOENT
    # in case of an error, followed by the elapsed time of the system call
    # (within angle bracets <>), if the elapsed time option was set. Between
    # these two, there could be extra information within brackets, eg a
    # desription of an error  or the labels of a flag value.
    #
    # Examles:
    # 16707 1371659593.864971 [b7726cb1] access("/etc/ld.so.nohwcap", F_OK) = -1 ENOENT (No such file or directory) <0.000023>
    # 16707 1371659593.868020 [b770e424] fcntl64(4, F_GETFL) = 0x402 (flags O_RDWR|O_APPEND) <0.000009>

    # the return part should be a positive number or a '-1' or a hex or a '?'
    r = line_parts["return"]
    assert r.isdigit() or r == '-1' or r == '?' or r.startswith("0x"), "Invalid format of return part in trace line `" + line + "`"

    # if the return part is a number let's cast it.
    if r.isdigit() or r == '-1':
      r = int(r)

    # now if the return part is -1 it should be accompanied with an error label
    # which should be the first part of the remaining_line.
    #
    # Example:
    # 14037 recv(6, 0xb7199058, 4096, 0) = -1 EAGAIN (Resource temporarily unavailable)
    error_label = None
    if r == -1:
      error_label, remaining_line = remaining_line.split(None, 1)

      # a basic check on the format of error label is whether it starts with 'E'
      # and it is all-caps.
      assert error_label.startswith('E') and error_label.isupper(), "Invalid format of error_label `" + error_label + "`"

    # In some rare cases, a syscall will not return but it will include an error
    # label.
    # 
    # Example:
    # 14037 <... poll resumed> )              = ? ERESTART_RESTARTBLOCK (To be restarted)
    if r == '?':
      remaining_line = remaining_line.strip()
      # if the remaining line starts with an 'E', then the return part contains
      # an error label.
      if remaining_line.startswith("E"):
        error_label, remaining_line = remaining_line.split(None, 1)
        assert error_label.startswith('E') and error_label.isupper(), "Invalid format of error_label `" + error_label + "`"

    # we can now form the complete syscall return part, which is the return
    # value of the syscall followed by the error label if one exists, or None if
    # it doesn't.
    line_parts["return"] = (r, error_label)

    # finally, if the elapsed_time option is set we should extract the elapsed
    # time data. Because the remaining line could optionally include some
    # unneeded information as shown in the examples above, we'll only extract
    # the data within the angle brackets. No elapsed time is provided in non
    # returning syscalls.
    if self.trace_options["elapsed_time"] and line_parts["return"] != ('?', None):
      line_parts["elapsed_time"] = float(remaining_line[remaining_line.rfind("<")+1:remaining_line.rfind(">")])

    line_parts = self._fix_args(line_parts)

    return line_parts



  def _parse_args(self, args_string):
    args_string = args_string.strip()

    # in unfinished system calls it is possible that the args_string will end
    # with a comma ","
    args_string = args_string.rstrip(",")

    if args_string == '':
      return []

    return _merge_quote_args(args_string.split(", "))



  def _fix_args(self, line_parts):
    """
    Fix the arguments of some specific system call.
    """

    # shutdown syscall includes both a number and a string description for the
    # "how" option. Change option number to its corresponding flag.
    #
    # Example shutdown syscall.
    # 7169  shutdown(5, 0 /* receive */) = 0
    #
    # In essence, treat:
    # 7169  shutdown(5, 0 /* receive */) = 0
    # as if it was:
    # 7169  shutdown(5, 0) = 0
    if line_parts["name"].startswith("shutdown"):
      # there are three possible options for shutdown.
      shutdown_flags = {0:'SHUT_RD', 1:'SHUT_WR', 2:'SHUT_RDWR'}
      # use the dictionary to change the option number to its corresponding flag
      # by parsing the option number. The option number is the first character
      # of the second argument in the args list.
      line_parts["args"][1] = shutdown_flags[int(line_parts["args"][1][0])]
    
    # Definition of restart_syscall:
    # long sys_restart_syscall(void);
    # 
    # Example of restart_syscall 
    # 14037 restart_syscall(<... resuming interrupted call ...>) = 1
    if line_parts["name"].startswith("restart_syscall"):
      # set arguments to the empty set since the provided message is not part of
      # the syscall's arguments list.
      line_parts["args"] = []

    """
    # system calls statfs64 or fstatfs64, sometimes include an 
    # unnecessary numeric value as their second parameter. Remove it.
    if syscall_name.startswith("statfs") or syscall_name.startswith("fstatfs"):
      # 22480 statfs64("/selinux", 84, {f_type="EXT2_SUPER_MAGIC", 
      # f_bsize=4096, f_blocks=4553183, f_bfree=741326, f_bavail=510030, 
      # f_files=1158720, f_ffree=509885, f_fsid={-1853641883, 
      # -1823071587}, f_namelen=255, f_frsize=4096}) = 0
      if parameters[1].isdigit():
        parameters.pop(1)


    # if the syscall is getdents, keep only the first and last parameters. These
    # are the file descriptor and the buffer size.
    if syscall_name.startswith("getdents"):
      parameters = [parameters[0], parameters[-1]]

    # TODO: add support for fcntl third parameter according to second parameter.
    if syscall_name.startswith("fcntl"):
      # keep only the first two paramenters
      parameters = [parameters[0], parameters[1]]

    # Get the return part.
    straceReturn = line[line.rfind('=')+1:].strip()
    if syscall_name.startswith("fcntl") and straceReturn.find("(flags ") != -1:
      # handle fcntl return part. I.e use the set of flags instead
      # of their hex representation.
      # example:
      # fcntl64(4, F_GETFL) = 0x402 (flags O_RDWR|O_APPEND)
      # replace the hex part: 0x402 with the flags O_RDWR|O_APPEND
      # get the part between '(flags' and ')'
      straceReturn = straceReturn[straceReturn.find("(flags ")+7:
                                  straceReturn.rfind(")")]
      straceReturn = (straceReturn, None)
    else:
      spaced_results = straceReturn.split(" ")
      if len(spaced_results) > 1:
        # keep only the first part.
        straceReturn = straceReturn[:straceReturn.find(" ")]
      try: 
        straceReturn = int(straceReturn) # result can also be a '?'
      except ValueError:
        pass
      # in case of an error include the error name as well.
      if straceReturn == -1 and len(spaced_results) > 1:
        straceReturn = (straceReturn, spaced_results[1])
      else:
        # if no error, use None as the second return value
        straceReturn = (straceReturn, None)
    """

    return line_parts



  def __repr__(self):
    # generate the trace options string.
    trace_options_string = ""
    if self.trace_options["inst_pointer"]:
      trace_options_string += "-i "
    if self.trace_options["timestamp"]:
      trace_options_string += "-" + self.trace_options["timestamp"] + " "
    if self.trace_options["elapsed_time"]:
      trace_options_string += "-T "
    if self.trace_options["output"]:
      trace_options_string += "-o "
    if self.trace_options["fork"]:
      trace_options_string += "-f"

    representation = "<StraceParser" \
                   + " trace_path=`" + self.trace_path + "`" \
                   + " trace_options=" + trace_options_string + ">"

    return representation



"""
Used to fix errors on parsed args. Specifically, if a string value in the trace
contains ", " the string will be wrongly split in two args. This method searches
for args that start with a double quote (indicating that the arg is a string)
and if that args does not end with a double quote (an unescaped double quote)
then the string must have been split. Join this args with the next one and
repeat the same procedure to fix.
"""
def _merge_quote_args(args):
  if len(args) <= 1:
    return args
  index = 0
  while index < len(args):
    # if the args starts with a quote but does not end with a quote, the
    # args must have been split wrong.
    if args[index].startswith("\""):
      while index+1 < len(args):
        if _ends_in_unescaped_quote(args[index].strip(".")):
          break
        args[index] += ", " + args[index+1]
        args.pop(index+1)
    index += 1

  return args


def _ends_in_unescaped_quote(string):
  if not string or string[-1] != '"':
    return False
  for index in range(-2, -len(string)-1, -1):
    if string[index] != '\\':
      return index % 2 == 0
  return False