from posix_omni_parser import Trace
import os


def get_test_data_path(filename):
  dir_path = os.path.dirname(os.path.realpath(__file__))
  return os.path.join(dir_path, filename)


class TestOpen():
  def test_open(self):
    strace_path = get_test_data_path("openclose.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    open_call = t.syscalls[0]

    assert open_call.name == "open"
    assert open_call.args[0].value == "test.txt"
    assert open_call.args[1].value == ["O_RDONLY"]
    assert open_call.args[2].value == ["0"]
    assert open_call.ret == (3, None)

    bad_open_call = t.syscalls[1]
    assert bad_open_call.ret == (-1, "ENOENT")


  def test_close(self):
    strace_path = get_test_data_path("openclose.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    close_call = t.syscalls[3]

    assert close_call.name == "close"
    assert close_call.args[0].value == 3
    assert close_call.ret == (0, None)
  
  #openat - open a file relative to a directory file descriptor
  def openat(self):
    strace_path = get_test_data_path("openclose.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    openat_call = t.syscalls[4]

    assert openat_call.args[0].value == "AT_FDCWD"
    assert openat_call.args[1].value == "/etc/ld.so.cache"
    assert openat_call.ret == (7, None)


class TestFstat():
  def test_fstat(self):
    strace_path = get_test_data_path("fstat.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    fstat_call = t.syscalls[0]

    assert fstat_call.name == "fstat"
    assert fstat_call.args[0].value == 3
    assert fstat_call.args[1].value[0] == "st_dev=makedev(0, 4)"
    assert fstat_call.args[1].value[5] == "st_gid=0"

class TestSocket():
  def test_socket(self):
    strace_path = get_test_data_path("socket.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    socket_call = t.syscalls[0]

    assert socket_call.name == "socket"
    assert socket_call.args[0].value == ["PF_INET"]
    assert socket_call.args[1].value == ["SOCK_STREAM"]
    assert socket_call.args[2].value == ["IPPROTO_IP"]
    assert socket_call.ret == (3, None)


class TestConnect():
  def test_connect(self):
    strace_path = get_test_data_path("socket.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    connect_call = t.syscalls[6]

    assert connect_call.args[0].value == 4
    assert connect_call.args[1].value[0].value == "AF_LOCAL"
    assert connect_call.args[1].value[1].value == "/var/run/nscd/socket"
    assert connect_call.args[2].value == 110
    assert connect_call.ret == (-1, "ENOENT")
