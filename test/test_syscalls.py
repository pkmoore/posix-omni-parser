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

  def test_stat(self):
    strace_path = get_test_data_path("fstat.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    stat_call = t.syscalls[1]
    assert stat_call.args[0].value == "/proc/19"
    assert stat_call.args[1].value[0] == 'st_dev=makedev(0, 0x16)'
    assert stat_call.args[1].value[5] == 'st_gid=0'
    assert stat_call.ret == (0, None)

  def test_lstat(self):
    strace_path = get_test_data_path("fstat.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    lstat_call = t.syscalls[2]
    assert lstat_call.args[0].value == "/proc/self/task"
    assert lstat_call.args[1].value[0] == 'st_dev=makedev(0, 0x16)'
    assert lstat_call.args[1].value[5] == 'st_gid=0'
    assert lstat_call.ret == (0, None)

  def test_statfs(self):
    strace_path = get_test_data_path("fstat.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    statfs_call = t.syscalls[3]
    assert statfs_call.args[0].value == "/sys/fs/selinux"
    assert statfs_call.args[1].value == '0x7ffffab26f40'
    assert statfs_call.ret == (-1, "ENOENT")

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

  #mark a socket as accepting connections
  def test_listen(self):
    strace_path = get_test_data_path("socket.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    listen_call = t.syscalls[11]
    assert listen_call.args[0].value == 7
    assert listen_call.args[1].value == 5
    assert listen_call.ret == (0, None)


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

class TestRead():
  
  def test_read(self):
    strace_path = get_test_data_path("readwrite.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    read_call = t.syscalls[0]

    assert read_call.args[0].value == 7
    assert read_call.args[1].value == '"hello world"'
    assert read_call.args[2].value == '1024'
    assert read_call.ret == (11, None)

    bad_read_call = t.syscalls[1]
    assert bad_read_call.args[0].value == 40
    assert bad_read_call.args[1].value == "0x7ffcf0e72860"
    assert bad_read_call.args[2].value == '10'
    assert bad_read_call.ret == (-1, "EBADF")
  
  def test_write(self):

    strace_path = get_test_data_path("readwrite.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    write_call = t.syscalls[2]

    assert write_call.args[0].value == 0
    assert write_call.args[1].value == '"Hello"'
    assert write_call.args[2].value == '5'
    assert write_call.ret == (5, None)

    bad_write_call = t.syscalls[3]
    assert bad_write_call.args[0].value == 40
    assert bad_write_call.args[1].value == '"Bad m"'
    assert bad_write_call.args[2].value == '5'
    assert bad_write_call.ret == (-1, "EBADF")

class TestExecve():
  
  def test_execve(self):

    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)

    execve_call = t.syscalls[0]
    assert execve_call.args[0].value == '/bin/ps'
    assert execve_call.args[1].value == '["ps"]'
    assert execve_call.args[2].value == 'NULL'
    assert execve_call.ret == (0, None)

  def test_get_pid(self):
    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)

    getpid_call = t.syscalls[1]
    assert getpid_call.ret == (21698, None)
  
  def test_get_euid(self):
    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)

    geteuid_call = t.syscalls[2]
    assert geteuid_call.ret == (0, None)
