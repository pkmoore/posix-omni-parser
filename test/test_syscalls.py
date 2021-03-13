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

class TestLseek():
  def test_lseek(self):
    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    lseek_call = t.syscalls[3]
    assert lseek_call.args[0].value == 3
    assert lseek_call.args[1].value == '0'
    assert lseek_call.args[2].value == ['SEEK_SET']
    assert lseek_call.ret == (0, None)

class TestClone():
  def test_clone(self):
    strace_path = get_test_data_path("clone.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    clone_call = t.syscalls[0]
    assert clone_call.args[0].value == ['child_stack=NULL']
    assert clone_call.args[1].value == 'flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD'
    assert clone_call.args[2].value == ['child_tidptr=0x7fdb04c07810']
    assert clone_call.ret == (21677, None)

class TestLink():
  def test_link(self):
    strace_path = get_test_data_path("link.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    link_call = t.syscalls[0]
    assert link_call.args[0].value == "al/ma/newfile.txt"
    assert link_call.args[1].value == "al/sic/newest1.txt"
    assert link_call.ret == (0, None)

    bad_link_call = t.syscalls[1]
    assert bad_link_call.args[0].value == "al/ma/newfile.txt"
    assert bad_link_call.args[1].value == "al/sic/"
    assert bad_link_call.ret == (-1, "EEXIST")

  def test_unlink(self):
    strace_path = get_test_data_path("link.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    unlink_call = t.syscalls[2]
    assert unlink_call.args[0].value == "al/sic/newest1.txt"
    assert unlink_call.ret == (0, None)

    bad_unlink_call = t.syscalls[3]
    assert bad_unlink_call.args[0].value == "al/sic/newest2.txt"
    assert bad_unlink_call.ret == (-1, "ENOENT")

class TestDir():
  def test_mkdir(self):
    strace_path = get_test_data_path("directory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    mkdir_call = t.syscalls[0]
    assert mkdir_call.args[0].value == "al/ma/new-dir1"
    assert mkdir_call.args[1].value == ['0700']
    assert mkdir_call.ret == (0, None)

    bad_mkdir_call = t.syscalls[1]
    assert bad_mkdir_call.args[0].value == "al/ma/new-dir1"
    assert bad_mkdir_call.args[1].value == ['0700']
    assert bad_mkdir_call.ret == (-1, "EEXIST")

  def test_rmdir(self):
    strace_path = get_test_data_path("directory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    rmdir_call = t.syscalls[2]
    assert rmdir_call.args[0].value == "al/ma/new-dir1"
    assert rmdir_call.ret == (0, None)

    bad_rmdir_call = t.syscalls[3]
    assert bad_rmdir_call.args[0].value == "al/ma/new-dir1"
    assert bad_rmdir_call.ret == (-1, "ENOENT")
  
  def test_chdir(self):
    strace_path = get_test_data_path("directory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    chdir_call = t.syscalls[4]
    assert chdir_call.args[0].value == "/home/almazhan/Desktop/res_tandon/posix-omni-parser/testbins"
    assert chdir_call.ret == (0, None)

    bad_chdir_call = t.syscalls[5]
    assert bad_chdir_call.args[0].value == "/home/almazhan/Desktop/res_tandon/posix-omni-parser/testbins1"
    assert bad_chdir_call.ret == (-1, "ENOENT")
  
  def test_getcwd(self):
    strace_path = get_test_data_path("directory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    getcwd_call = t.syscalls[6]
    assert getcwd_call.args[0].value == '"/home/almazhan/Desktop/res_tandon/posix-omni-parser/testbins"'
    assert getcwd_call.args[1].value == '4096'
    assert getcwd_call.ret == (61, None)

  #get directory entries label
  def test_getdents64(self): #Note: empty function
    strace_path = get_test_data_path("directory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    getdents64_call = t.syscalls[7]
    assert getdents64_call.args[0].value == 7
    assert getdents64_call.args[1].value == '[]'
    assert getdents64_call.args[2].value == 32768
    assert getdents64_call.ret == (0, None)

class TestMount():
  def test_mount(self):
    strace_path = get_test_data_path("mount.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    mount_call = t.syscalls[0]
    assert mount_call.args[0].value == '"none"'
    assert mount_call.args[1].value == '"/var/tmp"'
    assert mount_call.args[2].value == '"tmpfs"'
    assert mount_call.args[3].value == '0'
    assert mount_call.args[4].value == '"mode=0700,uid=65534"'
    assert mount_call.ret == (0, None)

    bad_mount_call = t.syscalls[1]
    assert bad_mount_call.args[0].value == '"al/ma/newest"'
    assert bad_mount_call.args[1].value == '"al/mnt"'
    assert bad_mount_call.args[2].value == 'NULL'
    assert bad_mount_call.args[4].value == 'NULL'
    assert bad_mount_call.ret == (-1, "EINVAL")

  def test_unmount(self):
    strace_path = get_test_data_path("mount.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    unmount_call = t.syscalls[2]
    assert unmount_call.args[0].value == '"/var/tmp"'
    assert unmount_call.args[1].value == ['0']
    assert unmount_call.ret == (0, None)

    bad_unmount_call = t.syscalls[3]
    assert bad_unmount_call.args[0].value == '"al/mnt/"'
    assert bad_unmount_call.args[1].value == ['0']
    assert bad_unmount_call.ret == (-1, "EINVAL")

class TestChmod():
  def test_chmod(self):
    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    chmod_call = t.syscalls[4]
    assert chmod_call.args[0].value == "al/ma/newfile.txt"
    assert chmod_call.args[1].value == ['0644']
    assert chmod_call.ret == (0, None)

    bad_chmod_call = t.syscalls[5]
    assert bad_chmod_call.args[0].value == "al/ma/newfile7.txt"
    assert bad_chmod_call.args[1].value == ['0644']
    assert bad_chmod_call.ret == (-1, "ENOENT")
  
  def test_access(self):
    strace_path = get_test_data_path("execve.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    bad_access_call = t.syscalls[6]
    assert bad_access_call.args[0].value == "/etc/ld.so.preload"
    assert bad_access_call.args[1].value == ["R_OK"]
    assert bad_access_call.ret == (-1, 'ENOENT')


class TestSignals():
   
  def test_sigaction(self): #Note-incorrect parsing
    strace_path = get_test_data_path("signals.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    sigaction_call = t.syscalls[0]
    assert sigaction_call.args[0].value == "SIGCHLD" 
    assert sigaction_call.args[1].value == "{sa_handler=0x55907f1f81c9"
    assert sigaction_call.args[2].value == "sa_mask=[CHLD]"
    assert sigaction_call.args[3].value == "sa_flags=SA_RESTORER|SA_RESTART"
    assert sigaction_call.args[4].value == 'sa_restorer=0x7ff1ed57f210}'
    assert sigaction_call.args[4].value == 'sa_restorer=0x7ff1ed57f210}'
    assert sigaction_call.args[8].value == '8'

    assert sigaction_call.ret == (0, None)

  def test_sigprocmask(self):
    strace_path = get_test_data_path("signals.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    sigprocmask_call = t.syscalls[1]
    assert sigprocmask_call.args[0].value == ["SIG_UNBLOCK"]
    assert sigprocmask_call.args[1].value == '[RTMIN RT_1]'
    assert sigprocmask_call.args[2].value == 'NULL'
    assert sigprocmask_call.args[3].value == '8'
    assert sigprocmask_call.ret == (0, None)

  def test_sigreturn(self):
    strace_path = get_test_data_path("signals.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    sigreturn_call = t.syscalls[2]
    assert sigreturn_call.args[0].value == "{mask=[]}"   
    assert sigreturn_call.ret == (26827, None)

class TestMemory():

  def test_mprotect(self):
    strace_path = get_test_data_path("memory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    mprotect_call = t.syscalls[0]
    assert mprotect_call.args[0].value == "0x7f3366ab3000"
    assert mprotect_call.args[1].value == '12288'
    assert mprotect_call.args[2].value == ['PROT_READ']
    assert mprotect_call.ret == (0, None)
  
  #create new mapping in the va space
  def test_mmap(self):
    strace_path = get_test_data_path("memory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    mmap_call = t.syscalls[1]
    assert mmap_call.args[0].value == "NULL"
    assert mmap_call.args[1].value == '2036952'
    assert mmap_call.args[2].value == ['PROT_READ']
    assert mmap_call.args[4].value == 7
    assert mmap_call.args[5].value == '0'
    assert mmap_call.ret == ('0x7fc88349b000', None)

  #delete mappings for specified address range
  def test_munmap(self):
    strace_path = get_test_data_path("memory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    munmap_call = t.syscalls[2]
    assert munmap_call.args[0].value == "0x7fcf9d4b0000"
    assert munmap_call.args[1].value == "75070"
    assert munmap_call.ret == (0, None)
  
  
  #set resource limits
  def test_prlimit64(self): #Note-incorrect parsing
    strace_path = get_test_data_path("memory.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    prlimit64_call = t.syscalls[3]
    assert prlimit64_call.args[0].value == 0
    assert prlimit64_call.args[1].value == ['RLIMIT_STACK']
    assert prlimit64_call.args[2].value == 'NULL'
    assert prlimit64_call.args[3].value == '{rlim_cur=8192*1024'
    assert prlimit64_call.ret == (0, None)

class TestSetup():
  #set segment size
  def test_brk(self):
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    brk_call = t.syscalls[0]
    assert brk_call.args[0].value == "NULL"
    assert brk_call.ret == ('0x56221d7d1000', None)

  #set pointer to thread ID
  def test_tid_addr(self):
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    set_tid_addr_call = t.syscalls[1]
    assert set_tid_addr_call.args[0].value == "7f75b62c36d0"
    assert set_tid_addr_call.ret == (29898, None)

  #set list of robust futexes
  def test_robust_list(self):
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    set_robust_list_call = t.syscalls[2]
    assert set_robust_list_call.args[0].value == "0x7f75b62c36e0"
    assert set_robust_list_call.args[1].value == "24"
    assert set_robust_list_call.ret == (0, None)

  #set architecture specific thread state
  def test_arch_prctl(self):
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    arch_prctl_call = t.syscalls[3]
    assert arch_prctl_call.args[0].value == ['ARCH_SET_FS']
    assert arch_prctl_call.args[1].value == '0x7f75b62c3400'
    assert arch_prctl_call.ret == (0, None)

    bad_arch_prctl_call = t.syscalls[4]
    assert bad_arch_prctl_call.args[0].value == ['0x3001 /* ARCH_??? */']
    assert bad_arch_prctl_call.args[1].value == '0x7ffcf11e3030'
    assert bad_arch_prctl_call.ret == (-1, 'EINVAL')

class TestMisc():
  #control device
  def test_ioctl(self): #Note-incorrect parsing
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    ioctl_call = t.syscalls[5]
    assert ioctl_call.args[0].value == 1
    assert ioctl_call.args[1].value == "TIOCGWINSZ"
    assert ioctl_call.args[2].value == "{ws_row=16"
    assert ioctl_call.args[3].value == "ws_col=109"
    assert ioctl_call.args[4].value == "ws_xpixel=0"
    assert ioctl_call.ret == (0, None)

  #read from a file descriptor at an offset
  def test_pread64(self):
    strace_path = get_test_data_path("misc.strace")
    syscall_definitions = get_test_data_path("syscall_definitions.pickle")
    t = Trace.Trace(strace_path, syscall_definitions)
    prlimit64_call = t.syscalls[6]
    assert prlimit64_call.args[0].value == 3
    assert prlimit64_call.args[2].value == '784'
    assert prlimit64_call.args[3].value == '64'
    assert prlimit64_call.ret == (784, None)

  
