"""
<Started>
  July 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>

    This module is responsible for converting different parameters within system
    calls into viable objects. This allows strace segments to not be interpeted
    as raw text, but rather a serializable structure that can be interpreted by
    syscallreplay.

"""
from __future__ import print_function

from builtins import str
from builtins import range
from builtins import object
import socket

DEBUG = False


class ParsingClass(object):
    def __repr__(self):
        return "<" + self.__class__.__name__ + " " + str(self.value) + ">"

    def __str__(self):
        return str(self.value)


# This class is used to wrap all arguments for which a specific type is not yet
# implemented.
class UnimplementedType(ParsingClass):
    def __init__(self, string_args):
        self.value = string_args.pop(0)


# This object is used to indicate that a system call did not return the expected
# value. This can happen for instance when a system call has an error, in which
# case values of structures are not returned.
# Example (fstat on success and on error):
# 19243 fstat64(3, {st_mode=S_IFREG|0644, st_size=98710, ...}) = 0 19243
# fstatfs(3, 0xbff476cc) = -1 EBADF (Bad file descriptor)
#
# The equality operator is overridden and only returns true if the  other object
# is of the same type. Less than and Greater than operators are also overridden
# and immediately raise an exception if used, since no such operations are
# allowed with this object.
class MissingValue(ParsingClass):
    def __init__(self, ev, string_args):
        self.expected_value = ev
        try:
            # this can happen when a structure is not dereferenced.
            self.given_value = string_args[0]
        except IndexError:
            # This case can occur when a value is missing entirely
            # Example open definition and strace output:
            #
            # int open(const char *pathname, int flags, mode_t mode);
            # 14037 open("/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
            #
            # Note how the parser expects a third argument for mode.
            self.given_value = None

    # override equality
    def __eq__(self, other):
        return type(other) is type(self)

    # override inequality
    def __ne__(self, other):
        return not self.__eq__(other)

    # override less than
    def __lt__(self, other):
        raise Exception(
            "Comparing object of type "
            + type(other)
            + " with "
            + self.__class__.__name__
            + " object."
        )

    # greater than behaves exactly like less than.
    def __gt__(self, other):
        return self.__lt__(other)

    # override representation and string
    def __repr__(self):
        return (
            "<"
            + self.__class__.__name__
            + " expected_value: "
            + str(self.expected_value)
            + ", given_value: "
            + str(self.given_value)
            + ">"
        )


class Int(ParsingClass):
    def __init__(self, string_args):
        temp_value = string_args.pop(0)

        # it is possible that a number is enclosed in square brackets '[]'. This
        # notation is used by strace to indicate pointer variables eg socklen_t
        # *addrlen
        if temp_value.startswith("[") and temp_value.endswith("]"):
            # remove the square brackets
            temp_value = temp_value[1:-1]

        try:
            temp_value = int(temp_value)
        except ValueError:
            raise Exception("Unexpected format when parsing Int:", temp_value)

        self.value = temp_value


class Hex(ParsingClass):
    def __init__(self, string_args):
        temp_value = string_args.pop(0)

        if temp_value.startswith("0x"):
            # remove 0x prefix
            temp_value = temp_value[2:]

        self.value = temp_value


class FileDescriptor(ParsingClass):
    def __init__(self, string_args):
        fd = string_args.pop(0)
        # pipe() fd array leaves brackets around its contents
        fd = fd.strip("[]")

        try:
            fd = int(fd)
        except ValueError:
            # AT_FDCWD is a valid value for the openat() file descriptor
            # parameter
            if fd != "AT_FDCWD":
                raise Exception("Unexpected format when parsing " "FileDescriptor:", fd)
        self.value = fd


class PollFD(ParsingClass):
    def __init__(self, fd, events, revents=None):

        # Definition of poll:
        # int poll(struct pollfd *fds, nfds_t nfds, int timeout)
        #
        # pollfd structure:
        # struct pollfd {
        #  int    fd;       /* file descriptor */
        #  short  events;   /* events to look for */
        #  short  revents;  /* events returned */
        # };
        #
        # Example poll trace (strace):
        # 26896 poll([{fd=4, events=POLLIN}, {fd=0, events=POLLIN}], 2, -1) = 1 ([{fd=4, revents=POLLIN}])

        # Note that revents is included in the result of the syscall trace and might not be
        # provided at all.
        self.value = [fd, events, revents]


class PollFDPointer(ParsingClass):
    def __init__(self, string_args):

        # Definition of poll:
        # int poll(struct pollfd *fds, nfds_t nfds, int timeout)
        #
        # pollfd structure:
        # struct pollfd {
        #  int    fd;       /* file descriptor */
        #  short  events;   /* events to look for */
        #  short  revents;  /* events returned */
        # };
        #
        # Example poll trace (strace):
        # 26896 poll([{fd=4, events=POLLIN}, {fd=0, events=POLLIN}], 2, -1) = 1 ([{fd=4, revents=POLLIN}])
        #
        # At this point this line will be partially edited to include the returned structure as part
        # of the input parameters. More specifically the revents parameters are moved after their
        # corresponding events parameters
        #
        # Example arguments:
        # ['[{fd=4', 'events=POLLIN}', 'revents=POLLIN}', '{fd=0', 'events=POLLIN}]', '2', '-1']

        # the first argument must start with "[{fd="
        assert string_args[0].startswith("[{fd="), "Unexpected argument in PollFD"

        # there may be multiple PollFD items like in the example above We will use a simple
        # structure of [PollFD1, PollFD2, etc]. We can further modularize this later.
        self.value = []

        # keep parsing until "]" is found indicating the end of the structure
        done = False
        while not done:

            # first argument is the fd of the pollfd structure
            fd = string_args.pop(0)

            # sanitize fd
            fd = fd.strip("[")[4:]
            try:
                fd = int(fd)
            except ValueError:
                raise Exception("Unexpected format when parsing fd in PollFD:", fd)

            # second argument is the events of the pollfd structure
            events = string_args.pop(0)

            # if events end with a closing square bracket (]) this must be the last pollfd structure
            # in the array so set the flag to exit the loop
            if events.endswith("]"):
                done = True

            # sanitize events
            events = events.strip("}]")[7:]

            revents = None
            if len(string_args) > 0 and string_args[0].startswith("revents="):
                revents = string_args.pop(0)
                revents = revents.strip("}")[8:]

            self.value.append(PollFD(fd, events, revents))


class Filepath(ParsingClass):
    def __init__(self, string_args):
        path = string_args.pop(0)
        # Remove quotes that surround paths for stored value
        if path[0] == '"' and path[-1] == '"':
            path = path[1:-1]
        self.value = path

    def __str__(self):
        # Converting a Filepath to a string restores the surrounding quotes
        return '"' + self.value + '"'


class Flags(ParsingClass):
    def __init__(self, string_args):
        # Deal with flags values strace doesn't support but storing their
        # numeric value as a string
        if len(string_args) == 1 and string_args[0].isdigit():
            self.value = [string_args.pop(0)]
        else:
            self.value = _string_to_flags(string_args.pop(0))

    def __str__(self):
        if len(self.value) == 1:
            return str(self.value[0])
        else:
            return "|".join(self.value)


class SockFamily(ParsingClass):
    """
    A SockFamily object can only appear as part of the Sockaddr object.
    """

    def __init__(self, value):
        if "sa_family=" not in value:
            raise Exception(
                "Unexpected argument when parsing SockFamily object: " + value
            )

        # get the part that comes after the 'sa_family=" label
        value = value[value.find("sa_family=") + 10 :]

        # a basic test.
        if not value.startswith("AF_") and not value.startswith("PF_"):
            raise Exception("Unknown Socket family: " + value)
        self.value = value


class SockPort(ParsingClass):
    """
    A SockPort object can only appear as part of the Sockaddr object.

    sin_port=htons(25588)
    """

    def __init__(self, value):
        if "sin_port=htons(" not in value:
            raise Exception(
                "Unexpected argument when parsing SockPort object: " + value
            )

        # get the part that comes between "sin_port=htons(" and ")". The remaining
        # value should be a number.
        try:
            value = int(value[value.find("sin_port=htons(") + 15 : value.rfind(")")])
        except:
            raise Exception("Unexpected argument when parsing SockPort object " + value)

        self.value = value


class SockIP(ParsingClass):
    """
    A SockPort object can only appear as part of the Sockaddr object.

    sin_addr=inet_addr("127.0.0.1")
    """

    def __init__(self, value):
        if 'sin_addr=inet_addr("' not in value:
            raise Exception("Unexpected argument when parsing SockIP object: " + value)

        # get the part that comes between sin_addr=inet_addr(" and ").
        try:
            value = value[value.find('sin_addr=inet_addr("') + 20 : value.rfind('")')]
        except:
            raise Exception("Unexpected argument when parsing SockIP object " + value)

        # Let's check if the value we have is indeed an IP address.
        try:
            socket.inet_aton(value)
        except socket.error:
            raise Exception("Value is not a valid IP address: " + value)

        self.value = value


class SockPath(ParsingClass):
    """
    A SockPath object can only appear as part of the Sockaddr object.
    """

    def __init__(self, value):
        # types of address paths (see "man 7 unix" for more information)
        #
        # unnamed:
        # 14039 getsockname(3, {sa_family=AF_FILE, NULL}, [2]) = 0
        # pathname:
        # 14037 connect(4, {sa_family=AF_FILE, path="/var/run/nscd/socket"}, 110) = -1 ENOENT
        # abstract:
        # 14037 connect(6, {sa_family=AF_FILE, path=@"/tmp/.X11-unix/X0"}, 20 )= 0
        #
        # for AF_LOCAL: sun
        # 11597 connect(4, {sa_family=AF_LOCAL, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)
        if value == "NULL":
            self.type = "unnamed"
            self.value = value
        elif value.startswith('path=@"'):
            self.type = "pathname"
            self.value = value[value.find('path=@"') + 7 : value.rfind('"}')]
        elif value.startswith("path="):
            self.type = "abstract"
            self.value = value[value.find('path="') + 6 : value.rfind('"}')]
        elif value.startswith("sun_path="):
            self.type = "sun"
            self.value = value[value.find('sun_path="') + 10 : value.rfind('"}')]
        else:
            raise Exception("Unexpected value when parsing SockPath object: " + value)

    def __repr__(self):
        return (
            "<"
            + self.__class__.__name__
            + " type: "
            + str(self.type)
            + " value: "
            + str(self.value)
            + ">"
        )


class SockData(ParsingClass):
    """
    A SockPath object can only appear as part of the Sockaddr object.
    """

    def __init__(self, value):
        # Example:
        # sa_data="\0\0\0\0\0\0\0\0\0\0\0\0\0\0"}

        assert value.startswith("sa_data="), "invalid SockData value"
        assert value.endswith("}"), "invalid SockGroups value"

        # geta data inside double quotes
        self.value = value[value.find('sa_data="') + 9 : -2]


class SockPid(ParsingClass):
    """
    A SockPid object can only appear as part of the Sockaddr object.
    """

    def __init__(self, value):

        # some bind() calls can either have "pid=0", or "nl_pid=0"
        assert value.startswith("pid=") or value.startswith(
            "nl_pid"
        ), "invalid SockPid value"

        try:
            self.value = int(value[value.find("pid=") + 4 :])
        except ValueError:
            raise Exception("Unexpected pid format: " + str(value))


class SockGroups(ParsingClass):
    """
    A SockGroups object can only appear as part of the Sockaddr object.
    """

    def __init__(self, value):

        # some bind() calls can either have "groups=00000000", or "nl_groups=00000000"
        assert value.startswith("groups=") or value.startswith(
            "nl_groups"
        ), "invalid SockGroups value"
        assert value.endswith("}"), "invalid SockGroups value"

        # remove closing curly bracket
        value = value[:-1]
        self.value = value[value.find("groups=") + 7 :]


class Sockaddr(ParsingClass):
    def __init__(self, string_args):
        self.value = None

        """
        Examples showing strace output of syscalls including the sockaddr structure:

        14039 getsockname(3, {sa_family=AF_FILE, NULL}, [2]) = 0
        14039 connect(3, {sa_family=AF_FILE, path=@"/tmp/.X11-unix/X0"}, 20)
        19176 bind(3, {sa_family=AF_INET, sin_port=htons(25588), sin_addr=inet_addr("127.0.0.1")}, 16) = 0

        11597 bind(3, {sa_family=AF_NETLINK, pid=0, groups=00000000}, 12) = 0
        11597 connect(4, {sa_family=AF_LOCAL, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)
        11597 connect(3, {sa_family=AF_UNSPEC, sa_data="\0\0\0\0\0\0\0\0\0\0\0\0\0\0"}, 16) = 0
        11597 connect(3, {sa_family=AF_INET6, sin6_port=htons(6666), inet_pton(AF_INET6, "::1", &sin6_addr), sin6_flowinfo=0, sin6_scope_id=0}, 28) = -1 ENETUNREACH (Network is unreachable)
        """

        # if the system call has an error, its structures are not dereferenced so we get the hex
        # number of the memory location of the structure. In this case we return immediately
        # leaving the self.value of the object to None, so that we can later identify this
        # condition.
        if string_args[0].startswith("0x"):
            return

        # 11597 accept(3, 0, NULL)                = 4
        if string_args[0] == "0":
            string_args.pop(0)
            self.value = "NULL"
            return

        # let's consume all the string_args that belong to the sockaddr structure.
        sockaddr_args = []
        sockaddr_args.append(string_args.pop(0))

        # the first argument of sockaddr should start with a '{'
        assert sockaddr_args[0].startswith("{"), (
            "First argument of sockaddr "
            + "structure does not start with a '{'"
            + "in arguments: "
            + str(sockaddr_args)
        )

        # and the last one should end with a '}'
        while True:

            # keep extracting tokens until the closing curly bracket is found
            sockaddr_args.append(string_args.pop(0))

            if sockaddr_args[-1].endswith("}"):
                break

        # Lets use these arguments to construct the value of the Sockaddr object.
        self.value = []

        # first item must show the sock address family
        sa_family = sockaddr_args.pop(0)
        self.value.append(SockFamily(sa_family))

        if sa_family.endswith("_FILE"):
            # sockaddr should include a path.
            # 14037 connect(6, {sa_family=AF_FILE, path=@"/tmp/.X11-unix/X0"}, 20 )= 0
            self.value.append(SockPath(sockaddr_args.pop(0)))
        elif sa_family.endswith("_LOCAL"):
            # sockaddr should include a path.
            # 11597 connect(4, {sa_family=AF_LOCAL, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)
            self.value.append(SockPath(sockaddr_args.pop(0)))
        elif sa_family.endswith("_UNSPEC"):
            # sockaddr should include data bytes.
            # 11597 connect(3, {sa_family=AF_UNSPEC, sa_data="\0\0\0\0\0\0\0\0\0\0\0\0\0\0"}, 16) = 0
            self.value.append(SockData(sockaddr_args.pop(0)))
        elif sa_family.endswith("_INET"):
            # sockaddr should include IP and port
            # 7123  bind(3, {sa_family=AF_INET, sin_port=htons(25588),
            #                        sin_addr=inet_addr("127.0.0.1")}, 16) = 0
            self.value.append(SockPort(sockaddr_args.pop(0)))
            self.value.append(SockIP(sockaddr_args.pop(0)))
        elif sa_family.endswith("_NETLINK"):
            # sockaddr should include pid and groups
            # 11597 bind(3, {sa_family=AF_NETLINK, pid=0, groups=00000000}, 12) = 0
            self.value.append(SockPid(sockaddr_args.pop(0)))
            self.value.append(SockGroups(sockaddr_args.pop(0)))
        else:
            if DEBUG:
                print(
                    'Socket address family "'
                    + sa_family
                    + '" of Sockaddr structure not fully parsed'
                )

            while len(sockaddr_args) > 0:
                self.value.append(sockaddr_args.pop(0))

        # there should be no more items in the sockaddr_args list
        assert (
            len(sockaddr_args) == 0
        ), "Additional arguments found when parsing Sockaddr object: " + str(
            sockaddr_args
        )


class Stat(ParsingClass):
    def __init__(self, string_args):
        self.value = None

        # Error condition, struct not parsed by strace.  Pointer value returned instead
        if string_args[0].startswith("0x"):
            return

        stat_args = []
        stat_args.append(string_args.pop(0))

        assert stat_args[0].startswith("{"), (
            "First argument of stat structure does not start with a '{'"
            + "in arguments: "
            + str(stat_args)
        )

        while True:
            stat_args.append(string_args.pop(0))

            if stat_args[-1].endswith("}"):
                break

        stat_args[0] = stat_args[0].lstrip("{")
        stat_args[-1] = stat_args[-1].rstrip("}")

        for i in range(len(stat_args)):
            if stat_args[i].startswith("st_dev=makedev("):
                stat_args[i] = stat_args[i] + ", " + stat_args[i + 1]
                stat_args.pop(i + 1)
                # break out here because we've shortened the list and will
                # get an index out of range if we continue
                break

        self.value = stat_args

        assert len(stat_args) == 15, (
            "We did not get 15 arguments for stat structure.  Got instead: "
            + str(len(stat_args))
            + "args -> "
            + str(stat_args)
        )

    def __str__(self):
        tmp = "{"
        tmp += ", ".join(self.value)
        tmp += "}"
        return tmp

    def __setitem__(self, index, value):
        self.value[index] = value

    def __getitem__(self, index):
        return self.value[index]


def _string_to_flags(flags_string):
    """
    Transforms a string to a list of flags.
    """
    flags_list = []

    # if no flags are set a zero is given. Return an empty list to indicate this.
    if flags_string == "0":
        return flags_list

    # A a list of flags can also contain a mode in its numeric value.
    #
    # Example:
    # 19243 fstat64(3, {st_mode=S_IFREG|0644, st_size=98710, ...}) = 0
    #
    # go through all flags and translate numeric mode to flags.
    for flag in flags_string.split("|"):
        if flag.isdigit():
            # if number it must be a mode. translate it to flags.
            flags_list += _mode_to_flags(int(flag))

        else:
            flags_list.append(flag)

    return flags_list


def _mode_to_flags(mode):
    """
    Transforms a number representing a mode to a list of flags.
    """
    mode = int(str(mode).strip("0"))

    mode_flags = {
        777: "S_IRWXA",
        700: "S_IRWXU",
        400: "S_IRUSR",
        200: "S_IWUSR",
        100: "S_IXUSR",
        70: "S_IRWXG",
        40: "S_IRGRP",
        20: "S_IWGRP",
        10: "S_IXGRP",
        7: "S_IRWXO",
        4: "S_IROTH",
        2: "S_IWOTH",
        1: "S_IXOTH",
    }

    list_of_flags = []
    # check for all permissions.
    if mode == 777:
        list_of_flags.append(mode_flags[777])
    else:
        # deal with each entity (digit) at a time (user then group
        # then other)
        mode_string = str(mode)
        # used to translate eg 7 to 700 for user.
        entity_position = 10 ** (len(mode_string) - 1)
        for mode_character in str(mode):
            try:
                entity = int(mode_character)
            except ValueError:
                raise Exception("Unexpected mode format: " + str(mode))

            # is the mode in the correct format?
            if entity < 0 or entity > 7:
                raise Exception("Unexpected mode format: " + str(mode))

            # check if current entity has all permissions
            if entity == 7:
                list_of_flags.append(mode_flags[entity * entity_position])
            else:
                # check entity for each flag.
                for flag in mode_flags:
                    if flag > 7 * entity_position or flag < entity_position:
                        continue
                    compare = int(str(flag).strip("0"))
                    if entity & compare == compare:
                        list_of_flags.append(mode_flags[flag])

            entity_position /= 10
    return list_of_flags


def _get_parsing_class(syscall_name, definition_parameter, value):
    """
    Examine the definition type to figure out which class should be used to
    describe this argument.
    """

    if definition_parameter.type == None:
        return UnimplementedType

    if definition_parameter.type == "char" and definition_parameter.pointer:
        # char pointer type
        if (
            "path" in definition_parameter.name
            or "filename" in definition_parameter.name
        ):
            # argument is a file path.
            return Filepath

    elif definition_parameter.type == "pollfd":
        # int poll(struct pollfd *fds, nfds_t nfds, int timeout)
        # 26896 poll([{fd=4, events=POLLIN}, {fd=0, events=POLLIN}], 2, -1) = 1 ([{fd=4, revents=POLLIN}])

        if not definition_parameter.pointer:
            raise Exception("non-pointer pollfd not supported")

        return PollFDPointer

    elif definition_parameter.type == "int" or definition_parameter.type.endswith("_t"):
        # number type
        if "fd" in definition_parameter.name:
            # argument is a file descriptor
            return FileDescriptor

        elif (
            "flag" in definition_parameter.name
            or "mode" in definition_parameter.name
            or "prot" in definition_parameter.name
            or "domain" in definition_parameter.name
        ):
            # argument is a set of flags.
            return Flags

        elif (
            "socket" in syscall_name
            and definition_parameter.type == "int"
            and "type" in definition_parameter.name
        ):
            return Flags

        elif definition_parameter.pointer:
            return Hex

        elif (
            definition_parameter.type == "off_t"
            or definition_parameter.type == "size_t"
        ):
            return Hex

        elif "|" in value or not value.isdigit():
            return Flags

        else:
            return Int

    elif definition_parameter.type == "sockaddr":
        # argument is a sockaddr
        return Sockaddr

    elif definition_parameter.struct == True and definition_parameter.type == "stat":
        return Stat

    if DEBUG:
        print(
            "No CLASS for: '"
            + definition_parameter.type
            + " "
            + definition_parameter.name
            + "' created yet :(\n"
        )

    return UnimplementedType


def _cast_syscall_arg(syscall_name, definition_parameter, string_args):
    # if the string_args list is empty, then the value is missing.
    if len(string_args) == 0:
        return MissingValue(definition_parameter, string_args)

    # detect the class to wrap this parameter in based on the definition of the parameter.
    parsing_class = _get_parsing_class(
        syscall_name, definition_parameter, string_args[0]
    )

    arg = parsing_class(string_args)

    if arg.value == None:
        # if the value of the argument is None, it means that the expected value was
        # not found. This can occur when a system call has an error in which case
        # structure and pointer values are not dereferenced, and instead we get the
        # hex value of its memory location.
        # Example:
        # 14037 recv(6, 0xb7199058, 4096, 0)      = -1 EAGAIN
        return MissingValue(definition_parameter, string_args)

    return arg


def cast_args(syscall_name, syscall_type, syscall_definitions, string_args):
    # we will consume these args (pop them off the list) so let's make a fresh
    # copy of them to avoid messing with the original list.
    string_args = string_args[:]

    if DEBUG:
        print("Syscall Name:", syscall_name)

    # find the syscall definition for this syscall.
    syscall_definition = None
    for sd in syscall_definitions:
        if syscall_name == sd.name or syscall_name.strip("_") == sd.name:
            syscall_definition = sd
            break

    if DEBUG:
        print("Syscall Name:", syscall_name)
    casted_args = []
    if syscall_definition.definition != None:
        for definition_parameter in syscall_definition.definition.parameters:
            if DEBUG:
                print("Definition Parameter:", definition_parameter)

            # for system calls that are unfinished we don't need to consider the
            # definition arguments beyond the number of arguments the unfinished syscall
            # includes. If this was not here, for every definition parameter for which
            # an argument is not provided in the unfinished system call a MissingValue
            # object would be used. This is not a bad idea (could even be usefull in
            # some cases) but it is a bit cleaner if we just ignore the missing
            # arguments.
            if syscall_type == "unfinished" and len(string_args) == 0:
                break
            ca = _cast_syscall_arg(syscall_name, definition_parameter, string_args)
            casted_args.append(ca)

    # Since not all arguments have a type corresponding to them (yet), and
    # because some argument values are part of the same syscall parameter (eg
    # structures may have multiple values) it is possible that there are still
    # arguments in the string_args list that are not consumed. Let's wrap them
    # in an UnimplementedType class and append them at the end of the
    # casted_args list.
    while len(string_args) > 0:
        # remember that casting to a class automatically consumes items from the
        # given list
        casted_args.append(UnimplementedType(string_args))

    casted_args = tuple(casted_args)

    return casted_args
