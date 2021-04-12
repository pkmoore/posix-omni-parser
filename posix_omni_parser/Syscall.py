"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>


"""
from __future__ import absolute_import

from builtins import str
from builtins import object
from . import parsing_classes

DEBUG = False


class UnfinishedSyscall(object):
    """
    If a syscall is interrupted or blocked, it will be split in multiple lines.
    This object is used to store the partial system call information included in
    the unfinished syscall.

    Example from strace output:
    19176 accept(3, <unfinished ...>
    19175 connect(5, {sa_family=AF_INET, sin_port=htons(25588),
                      sin_addr=inet_addr("127.0.0.1")}, 16) = 0
    19176 <... accept resumed> {sa_family=AF_INET, sin_port=htons(42572),
                                sin_addr=inet_addr("127.0.0.1")}, [16]) = 4
    """

    def __init__(self, pid, name, args):
        self.pid = pid
        self.name = name
        self.args = args

    def __eq__(self, other):
        """
        Equality of Unfinished system calls is based on the pid and the name of the
        system call.
        """
        return self.pid == other.pid and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "UnfinishedSyscall: " + self.pid + " " + self.name + " " + str(self.args)


class Syscall(object):
    """
    <Purpose>
      This object is used to describe a system call, holding all the information
      extracted from the trace file. The same object is used to describe system
      calls independently on which utility was used to generate the trace file.

    <Attributes>
      self.original_line:
        A string holding the original line from which this object was created.

      self.type:
        The type of the system call. This can be one of the UNFINISHED, RESUMED or
        COMPLETE.

      self.pid:
        The process id of this system call.

      self.name:
        The name of the system call.

      self.args:
        A tuple containing all the arguments of the system call. The value of each
        argument can be either a string or wrapped into a more meaningful class.

      self.ret:
        A tuple holding the return part of the system call. This tuple should
        always contain two items. The first one is the return value of the system
        call. The second is either a string holding the error label eg "EACCES"
        in case the system call had an error or None if the syscall executed
        correctly.

      self.inst_pointer:
        The instruction pointer at the time of the system call.

      self.timestamp:
        This value can have different formats and content according to the parser
        options. For example it can hold  a relative timestamp indicating the
        interval between the beginning of successive syscalls or it can hold the
        time the syscall was executed.

      self.elapsed_time:
        The time difference between the beginning and the end of the system call.
    """

    # System call types.

    # an unfinished system call
    UNFINISHED = 0

    # a resuming syscall. Its unfinished version must have been met earlier.
    RESUMED = 1

    # a directly completed syscall. That is, there was no intermediate unfinished
    # step. A resumed and a complete syscall are essentially the same in terms of
    # the information they hold but the type indicates this distinction between
    # them.
    COMPLETE = 2

    def __init__(self, syscall_definitions, line, line_parts):
        """
        <Purpose>
          Initialize a Syscall object. Create the data fields of the object. If the
          information needed for a data field is not given, set the value of that
          data field to None. Cast the system call arguments into meaningful
          classes.

        <Arguments>
          syscall_definitions:
            A list of system call definitions used to parse the arguments of the
            system call into more meaningful classes.

          line:
            The original line from which the Syscall object is derived.

          line_parts:
            A list containing the parts of the trace line. E.g: type, pid, name,
            args, return, timestamp, etc ...

        <Exceptions>
          None

        <Side Effects>
          None

        <Returns>
          None
        """

        self.original_line = line

        # TODO: better use an enum here
        self.type = line_parts["type"]
        assert (
            self.type == Syscall.UNFINISHED
            or self.type == Syscall.RESUMED
            or self.type == Syscall.COMPLETE
        ), "Unrecognized syscall type"

        self.pid = line_parts["pid"]
        self.name = line_parts["name"]

        # at this point all system call arguments are represented as strings. Let's
        # cast them into more meaningful classes.

        # when casting arguments, a comparsion against our pickle file is made. If
        # rr has injected its own syscalls within the trace, we skip this part
        # and set the self.args parameter to an arbitrary None, as we don't care
        # about it.
        if "syscall_" not in self.name:
            self.args = parsing_classes.cast_args(
                self.name, line_parts["type"], syscall_definitions, line_parts["args"]
            )
        else:
            self.args = None

        self.ret = line_parts["return"]

        self.timestamp = None
        self.inst_pointer = None
        self.elapsed_time = None

        if "timestamp" in line_parts:
            self.timestamp = line_parts["timestamp"]

        if "inst_pointer" in line_parts:
            self.inst_pointer = line_parts["inst_pointer"]

        if "elapsed_time" in line_parts:
            self.elapsed_time = line_parts["elapsed_time"]

    def isSuccessful(self):
        """
        If the first item of the return part is -1 or ? it means the syscall
        returned an error or did not return. Otherwise it was successful.
        """
        return self.ret[0] != -1 and self.ret[0] != "?"

    def __repr__(self):

        types = {
            Syscall.UNFINISHED: "unfinished",
            Syscall.RESUMED: "resumed",
            Syscall.COMPLETE: "complete",
        }

        type_string = types[self.type]

        representation = (
            "ORIGINAL LINE: "
            + self.original_line
            + "\n"
            + "TYPE:          "
            + type_string
            + "\n"
            + "PID:           "
            + str(self.pid)
            + "\n"
            + "NAME:          "
            + self.name
            + "\n"
            + "ARGS:          "
            + str(self.args)
            + "\n"
            + "RETURN:        "
            + str(self.ret)
            + "\n"
        )
        if self.inst_pointer:
            representation += "INST_POINTER: " + self.inst_pointer + "\n"
        if self.timestamp:
            representation += "TIMESTAMP: " + str(self.timestamp) + "\n"
        if self.elapsed_time:
            representation += "ELAPSED_TIME: " + str(self.elapsed_time) + "\n"

        return representation
