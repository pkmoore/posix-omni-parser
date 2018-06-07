"""
<Started>
  Sept 2013

<Author>
  Savvas Savvides <savvas@purdue.edu>

<Purpose>
  This plug-in is used to reform the generic format of posix-omni-parser to the
  format checkAPI requires.

  Formating changes:
  - Limit system calls to a list of handled system calls.
    --> keep only the system calls whose name appears in the handled_syscalls 
        directory below.

  - Move result parameters to the return part of the syscall.
    --> For example the accept system call usually looks something like this:
        accept(3, {sa_family=AF_INET, sin_port=htons(42572), sin_addr=inet_addr("127.0.0.1")}, [16]) = 4
    --> which will result in a Syscall object of:
        name = accept, args = (FD(3), SOCKADDR(AF_INET, 42572, "127.0.0.1"), 16), 
        ret = (4, None) -- this is a rough representation of the Syscall object.
    --> the sockaddr and addrlen arguments are result arguments so we want to 
        move these two arguments to the result so we get the following:
        name = accept, args = (FD(3)), ret = (4, (SOCKADDR(AF_INET, 42572, "127.0.0.1"), 16)))

  - Generate a trace bundle.

"""

# system calls handled in checkAPI. Listed in alphabetical order and including
# their definition (Ubuntu Linux kernel 3.0.5) followed by examples of strace
# output for that syscall.
#
# Each syscall has a list which indicates the positions of the return arguments
# that should be moved to the return part of the syscall. Empty list means no
# rearrangement is necessary. A list of [1,2] means that the second and third 
# arguments should be moved to the return part.
handled_syscalls = {
  # int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
  # 
  # Example strace output:
  # 19176 accept(3, {sa_family=AF_INET, sin_port=htons(42572),
  #              sin_addr=inet_addr("127.0.0.1")}, [16]) = 4
  "accept" : [],

  # int access(const char *pathname, int mode);
  # 
  # Example strace output:
  # 19178 access("syscalls.txt", F_OK) = 0
  # 19178 access("syscalls.txt", R_OK|W_OK) = 0
  # 19178 access("syscalls.txt", X_OK) = -1 EACCES (Permission denied)
  "access" : [],

  # int bind(int sockfd, const struct sockaddr *addr, 
  #          socklen_t addrlen);
  # 
  # Example strace output:
  # 19176 bind(3, {sa_family=AF_INET, sin_port=htons(25588), 
  #                sin_addr=inet_addr("127.0.0.1")}, 16) = 0
  # 19184 bind(3, {sa_family=AF_INET, sin_port=htons(25588), 
  #                sin_addr=inet_addr("127.0.0.1")}, 16) = -1 
  #                         EADDRINUSE (Address already in use)
  "bind" : [],
  
  # int chdir(const char *path);
  # 
  # Example strace output:
  # 19217 chdir(".") = 0
  "chdir" : [],

  # int clone(int (*fn)(void *), void *child_stack, int flags, 
  #           void *arg, ... /* pid_t *ptid, struct user_desc *tls, 
  #           pid_t *ctid */ );
  # 
  # Example strace output:
  # 7122 clone(child_stack=0xb7507464, 
  #            flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|
  #                  CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|
  #                  CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID, 
  #            parent_tidptr=0xb7507ba8, {entry_number:6, 
  #            base_addr:0xb7507b40, limit:1048575, seg_32bit:1, 
  #            contents:0, read_exec_only:0, limit_in_pages:1, 
  #            seg_not_present:0, useable:1}, 
  #            child_tidptr=0xb7507ba8) = 7123
  "clone" : [],

  # int close(int fd);
  # 
  # Example strace output:
  # 19319 close(3) = 0
  "close" : [],

  # int connect(int sockfd, const struct sockaddr *addr, 
  #             socklen_t addrlen);
  # 
  # Example strace output:
  # 19175 connect(5, {sa_family=AF_INET, sin_port=htons(25588), 
  #                   sin_addr=inet_addr("127.0.0.1")}, 16) = 0
  # 19262 connect(5, {sa_family=AF_INET, sin_port=htons(25588), 
  #                   sin_addr=inet_addr("127.0.0.1")}, 16) = -1 
  #                             ECONNREFUSED (Connection refused)
  "connect" : [],

  # int creat(const char *pathname, mode_t mode);
  # 
  # Example strace output:
  # 19229 creat("syscalls.txt", 0666)       = 3
  # 19229 creat("syscalls2.txt", 0600)      = 4
  "creat" : [],

  # int dup(int oldfd);
  # 
  # Example strace output:
  # 19231 dup(3) = 4
  # 19231 dup(3) = -1 EBADF (Bad file descriptor)
  "dup" : [],

  # int dup2(int oldfd, int newfd);
  # 
  # Example strace output:
  # 19233 dup2(3, 4) = 4
  # 19233 dup2(3, 3) = 3
  # 19233 dup2(3, -1) = -1 EBADF (Bad file descriptor)
  "dup2" : [],

  # int dup3(int oldfd, int newfd, int flags);
  # 
  # Example strace output:
  # 19235 dup3(3, 4, O_CLOEXEC) = 4
  "dup3" : [],

  # int fcntl(int fd, int cmd, ... /* arg */ );
  # 
  # TODO: add support for third parameter of fcntl
  #
  # Example strace output:
  # 19239 fcntl64(3, F_GETFL) = 0 (flags O_RDONLY)
  # 19239 fcntl64(4, F_GETFL) = 0x402 (flags O_RDWR|O_APPEND)
  "fcntl" : [],

  # int fstat(int fd, struct stat *buf);
  # 
  # Example strace output:
  # 10605 fstat64(3, {st_dev=makedev(8, 6), st_ino=697814, 
  #                   st_mode=S_IFREG|0664, st_nlink=1, st_uid=1000, 
  #                   st_gid=1000, st_blksize=4096, st_blocks=0, 
  #                   st_size=0, st_atime=2013/03/06-00:17:54, 
  #                   st_mtime=2013/03/06-00:17:54, 
  #                   st_ctime=2013/03/06-00:17:54}) = 0
  # 32566 fstat64(0, {st_dev=makedev(0, 11), st_ino=8, 
  #               st_mode=S_IFCHR|0620, st_nlink=1, st_uid=1000, 
  #               st_gid=5, st_blksize=1024, st_blocks=0, 
  #               st_rdev=makedev(136, 5), 
  #               st_atime=2013/03/05-11:15:44, 
  #               st_mtime=2013/03/05-11:15:44, 
  #               st_ctime=2013/03/05-10:44:02}) = 0
  # 10605 fstat64(3, 0xbfb99fe0) = -1 EBADF (Bad file descriptor)
  "fstat" : [],

  # int fstatfs(int fd, struct statfs *buf);
  # 
  # Example strace output:
  # 19243 fstatfs(3, {f_type="EXT2_SUPER_MAGIC", f_bsize=4096, 
  #    f_blocks=4553183, f_bfree=1457902, f_bavail=1226606, 
  #    f_files=1158720, f_ffree=658673, f_fsid={-1853641883, 
  #    -1823071587}, f_namelen=255, f_frsize=4096}) = 0
  "fstatfs" : [],

  # int getdents(unsigned int fd, struct linux_dirent *dirp, 
  #              unsigned int count);
  # 
  # Example strace output:
  # 10917 getdents(3, {{d_ino=709301, d_off=2124195000, d_reclen=28, 
  #                d_name="sendto.strace"} {d_ino=659266, 
  #                d_off=2147483647, d_reclen=32, 
  #                d_name="syscalls_functions.h"}}, 1024) = 60
  # 10917 getdents(3, {}, 1024) = 0
  "getdents" : [],

  # int   getpeername(int sockfd, struct sockaddr *addr, 
  #                   socklen_t *addrlen);
  # 
  # Example strace output:
  # 19252 getpeername(5, {sa_family=AF_INET, sin_port=htons(25588), 
  #                   sin_addr=inet_addr("127.0.0.1")}, [16]) = 0
  "getpeername" : [],

  # int getsockname(int sockfd, struct sockaddr *addr, 
  #                 socklen_t *addrlen);
  # 
  # Example strace output:
  # 19255 getsockname(3, {sa_family=AF_INET, sin_port=htons(0), 
  #                   sin_addr=inet_addr("0.0.0.0")}, [16]) = 0
  "getsockname" : [],

  # int getsockopt(int sockfd, int level, int optname, void *optval, 
  #                socklen_t *optlen);
  # 
  # Example strace output:
  # 19258 getsockopt(3, SOL_SOCKET, SO_TYPE, [1], [4]) = 0
  # 19258 getsockopt(3, SOL_SOCKET, SO_OOBINLINE, [0], [4]) = 0
  "getsockopt" : [],

  # int ioctl(int d, int request, ...);
  # 
  # ioctl(0, SNDCTL_TMR_TIMEBASE or TCGETS, {c_iflags=0x6d02, 
  #       c_oflags=0x5, c_cflags=0x4bf, c_lflags=0x8a3b, c_line=0, 
  #       c_cc="\x03\x1c\x7f\x15\x017\x16\xff\x00\x00"}) = 0
  # ioctl(3, SNDCTL_TMR_TIMEBASE or TCGETS, 0xbfda9e08) 
  #                    = -1 ENOTTY (Inappropriate ioctl for device)
  # 
  "ioctl" : [],

  # int link(const char *oldpath, const char *newpath);
  # 
  # Example strace output:
  # 19260 link("syscalls.txt", "syscalls.link") = -1 
  #            EEXIST (File exists)
  # 19260 link("hopefully_no_such_filename_exists.txt", 
  #         "syscalls2.link") = -1 ENOENT (No such file or directory)
  "link" : [],

  # int listen(int sockfd, int backlog);
  # 
  # Example strace output:
  # 19176 listen(3, 5) = 0
  "listen" : [],

  # off_t lseek(int fd, off_t offset, int whence);
  # 
  # Example strace output:
  # 19265 lseek(3, 1, SEEK_SET) = 1
  # 19265 lseek(3, 5, SEEK_CUR) = 16
  "lseek" : [],
  
  # int mkdir(const char *pathname, mode_t mode);
  # 
  # Example strace output:
  # 19269 mkdir("syscalls_dir", 0775) = -1 EEXIST (File exists)
  "mkdir" : [],

  # int open(const char *pathname, int flags);
  # int open(const char *pathname, int flags, mode_t mode);
  # 
  # Example strace output:
  # 19224 open("syscalls.txt", O_RDONLY|O_CREAT, 0664) = 3
  # 19224 open("syscalls2.txt", O_RDWR|O_CREAT|O_APPEND, 0664) = 3
  "open" : [],

  # ssize_t read(int fd, void *buf, size_t count);
  # 
  # Example strace output:
  # 19282 read(3, "abcdefghijklmnopqrst", 20) = 20
  "read" : [],

  # ssize_t recv(int sockfd, void *buf, size_t len, int flags);
  # 
  # Example strace output:
  # 19284 recv(5, "Message to be received.\0", 24, 0) = 24
  "recv" : [],

  # ssize_t recvfrom(int sockfd, void *buf, size_t len, int flags,
  #                  struct sockaddr *src_addr, socklen_t *addrlen);
  # 
  # Example strace output:
  # 19294 recvfrom(3, "Message for sendto.\0", 512, 0, 
  #                {sa_family=AF_INET, sin_port=htons(40299), 
  #                sin_addr=inet_addr("127.0.0.1")}, [16]) = 20
  "recvfrom" : [],

  # ssize_t recvmsg(int sockfd, struct msghdr *msg, int flags);
  # 
  # Example strace output:
  # recvmsg(4, {msg_name(12)={sa_family=AF_NETLINK, pid=0, 
  #         groups=00000000}, msg_iov(1)=[{"\24\0\0gmai", 4096}], 
  #         msg_controllen=0, msg_flags=0}, 0) = 20
  "recvmsg" : [],

  # int rmdir(const char *pathname);
  # 
  # Example strace output:
  # 19302 rmdir("syscalls_dir") = 0
  "rmdir" : [],

  # int select(int nfds, fd_set *readfds, fd_set *writefds,
  #                fd_set *exceptfds, struct timeval *timeout);
  # 
  # select(0, NULL, NULL, NULL, {1, 0})     = 0 (Timeout)
  # select(0, NULL, NULL, NULL, {1, 0})     = 0 (Timeout)
  "select" : [],

  # ssize_t send(int sockfd, const void *buf, size_t len, int flags);
  # 
  # Example strace output:
  # 19285 send(4, "Message to be received.\0", 24, 0) = 24
  # 19304 send(5, "\0\0c\364", 4, 0)        = -1 EPIPE (Broken pipe)
  "send" : [],

  # ssize_t sendmsg(int sockfd, const struct msghdr *msg, int flags);
  # 
  # Example strace output:
  # 19307 sendmsg(3, {msg_name(16)={sa_family=AF_INET, 
  #               sin_port=htons(25588), 
  #               sin_addr=inet_addr("127.0.0.1")}, 
  #               msg_iov(1)=[{"Message for sendmsg.\0", 21}], 
  #               msg_controllen=0, msg_flags=0}, 0) = 21
  #
  # 14040 sendmsg(8, {msg_name(0)=null, msg_iov(1)=[{"\0", 1}], 
  #    msg_controllen=24, {cmsg_len=24, cmsg_level=sol_socket, 
  #    cmsg_type=scm_credentials{pid=14037, uid=1000, gid=1000}}, 
  #    msg_flags=0}, MSG_NOSIGNAL)     
  "sendmsg" : [],

  # ssize_t sendto(int sockfd, const void *buf, size_t len, 
  #                int flags, const struct sockaddr *dest_addr, 
  #                socklen_t addrlen);
  # 
  # Example strace output:
  # 19309 sendto(3, "Message for sendto.\0", 20, 0, 
  #              {sa_family=AF_INET, sin_port=htons(25588), 
  #              sin_addr=inet_addr("127.0.0.1")}, 16) = 20
  "sendto" : [],

  # int setsockopt(int sockfd, int level, int optname, void *optval, 
  #                socklen_t optlen);
  # 
  # Example strace output:
  # 19313 setsockopt(3, SOL_SOCKET, SO_REUSEADDR, [1], 4) = 0
  "setsockopt" : [],

  # int shutdown(int sockfd, int how);
  # 
  # Example strace output:
  # 19316 shutdown(5, 0 /* receive */) = 0
  # 19316 shutdown(5, 2 /* send and receive */) = 0
  "shutdown" : [],

  # int socket(int domain, int type, int protocol);
  # 
  # Example strace output:
  # 19176 socket(PF_INET, SOCK_STREAM, IPPROTO_IP) = 3
  # 19294 socket(PF_INET, SOCK_DGRAM, IPPROTO_UDP) = 3
  "socket" : [],

  # int stat(const char *path, struct stat *buf);
  # 
  # Example strace output:
  # 10538 stat64("syscalls.txt", {st_dev=makedev(8, 6), st_ino=697814,
  #    st_mode=S_IFREG|0664, st_nlink=1, st_uid=1000, st_gid=1000, 
  #    st_blksize=4096, st_blocks=0, st_size=0, 
  #    st_atime=2013/03/06-00:17:54, st_mtime=2013/03/06-00:17:54, 
  #    st_ctime=2013/03/06-00:17:54}) = 0
  # 19321 stat64("hopefully_no_such_filename_exists.txt", 
  #              0xbf8c7d50) = -1 ENOENT (No such file or directory)
  #
  # Example truss output:
  # 2303: stat64("/savvas/syscalls", 0x08047130)    = 0
  # 2303:     d=0x00780000 i=299777 m=0100755 l=1  u=0     g=0     sz=59236
  # 2303:   at = Apr 25 22:54:48 EDT 2013  [ 1366944888.736170000 ]
  # 2303:   mt = Apr 25 21:43:45 EDT 2013  [ 1366940625.857272000 ]
  # 2303:   ct = Apr 25 21:43:45 EDT 2013  [ 1366940625.857272000 ]
  # 2303:     bsz=8192  blks=116   fs=ufs
  "stat" : [],

  # int statfs(const char *path, struct statfs *buf);
  # 
  # Example strace output:
  # 19323 statfs("syscalls.txt", {f_type="EXT2_SUPER_MAGIC", 
  #     f_bsize=4096, f_blocks=4553183, f_bfree=1458896, 
  #     f_bavail=1227600, f_files=1158720, f_ffree=658713, 
  #     f_fsid={-1853641883, -1823071587}, f_namelen=255, 
  #     f_frsize=4096}) = 0
  "statfs" : [],

  # int symlink(const char *oldpath, const char *newpath);
  # 
  # Example strace output:
  # 19267 symlink("syscalls.txt", "syscalls.symlink") = 0
  "symlink" : [],

  # int unlink(const char *pathname);
  # 
  # Example strace output:
  # 19327 unlink("syscalls.txt") = 0
  # 19327 unlink("syscalls.symlink")        = 0
  # 19327 unlink("hopefully_no_such_filename_exists.txt") = -1 ENOENT 
  #                                    (No such file or directory)
  "unlink" : [],

  # ssize_t write(int fd, const void *buf, size_t count);
  # 
  # Example strace output:
  # 19265 write(3, "abcdefghijklmnopqrstuvwxyz", 26) = 26
  "write" : []
}



def main():
  trace = Trace(sys.argv[1])
  syscalls = trace.syscalls

  # remove system calls that are not handled by checkAPI
  index = 0
  while index < len(syscalls):
    if syscalls[index].name not in handled_syscalls.keys:
      syscalls.pop(index)
    else:
      index += 1
  
  """
  Move result parameters to the result part.

  Some of the parameters in Syscall object:
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
  """
  for syscall in syscalls:
    # we only want to move arguments to the return type if the syscall is
    # successful.
    if syscall.isSuccessful():
      # so it must be the case that the second item in return part is None
      if syscall.ret[1] != None:
        raise Exception("Unexpected format of return part when rearranging syscall.")
      
      ret_args = () # a tuple to be added as the second item in return part.
      args = list(syscall.args)
      for argument_index in handled_syscalls[syscall.name]:
        # insert argument to the ret_args tuple.
        ret_args = ret_args + (args.pop(argument_index),)
      
      # update the arguments of the system call
      syscall.args = tuple(args)

      # and set the new return part.
      syscall.ret = (syscall.ret[0], ret_args)



if __name__ == "__main__":
  main()
