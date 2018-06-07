"""Install posix omni parser
"""

from distutils.core import setup

setup(name='posix_omni_parser',
      version='1.0',
      description='posix-omni-parser',
      author='Savvas Savvides',
      author_email='',
      url='https://github.com/pkmoore/posix-omni-parser',
      packages=['posix_omni_parser',
                'posix_omni_parser.parsers',
                'sysDef'])
