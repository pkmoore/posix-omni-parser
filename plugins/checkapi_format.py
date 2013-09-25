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
  - Move result parameters to the return part of the syscall.
  - Generate a trace bundle.

"""


hadled_syscalls = [

]

def main():
  trace = Trace(sys.argv[1])
  syscalls = trace.syscalls




if __name__ == "__main__":
  main()