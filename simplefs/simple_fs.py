import os

SFS_METADATA_FILENAME = 'sfs.metadata'
SFS_DATA_PREFIX = 'sfs_data.'
ROOT_DIRECTORY_INODE = 1

filesystemmetadata = {}

# fast lookup table...   (Should I deprecate this?)
fastinodelookuptable = {}


def blank_fs_init():
  """
  <Purpose>
    Initialize a blank file system.

  <Arguments>
    None

  <Exceptions>
    None
  
  <Side Effects>
    None

  <Returns>
    None
  """

  for filename in os.listdir():
    if filename.startswith(DATA_PREFIX) and os.path.isfile(filename):
      os.remove(filename)

  # Now setup blank data structures
  filesystemmetadata['nextinode'] = 3
  filesystemmetadata['dev_id'] = 20
  filesystemmetadata['inodetable'] = {}
  filesystemmetadata['inodetable'][ROOT_DIRECTORY_INODE] = {
    'size':0, 
    'uid':DEFAULT_UID, 
    'gid':DEFAULT_GID, 
    'mode':S_IFDIR | S_IRWXA, # directory + all permissions
    'atime':1323630836, 
    'ctime':1323630836, 
    'mtime':1323630836,
    'linkcount':2,    # the number of dir entries...
    'filename_to_inode_dict': {'.':ROOT_DIRECTORY_INODE, '..':ROOT_DIRECTORY_INODE}
  }
    
  fastinodelookuptable['/'] = ROOT_DIRECTORY_INODE

  _persist_metadata(METADATAFILENAME)



def _persist_metadata(metadatafilename):
  """
  <Purpose>
    Write metadata information to a file.

  <Arguments>
    metadatafilename:
      The metadata file name in which we want to store the metadata.

  <Exceptions>
    IOError
  
  <Side Effects>
    None

  <Returns>
    None
  """

  metadatastring = serialize.serializedata(filesystemmetadata)

  try:
    meta_file = open(metadatafilename, 'w')
    meta_file.write(metadatastring)
  finally:
    meta_file.close()



def _restore_metadata(metadatafilename):
  """
  <Purpose>
    Write metadata information to a file.

  <Arguments>
    metadatafilename:
      The metadata file name from which we want to read the metadata.

  <Exceptions>
    IOError
  
  <Side Effects>
    None

  <Returns>
    None
  """

  # should only be called with a fresh system...
  assert(filesystemmetadata == {})

  try:
    meta_file = open(metadatafilename)
    metadatastring = meta_file.read()
  finally:
    meta_file.close()

  # get the dict we want
  desiredmetadata = serialize.deserializedata(metadatastring)

  # I need to put things in the dict, but it's not a global...   so instead
  # add them one at a time.   It should be empty to start with
  for item in desiredmetadata:
    filesystemmetadata[item] = desiredmetadata[item]

  # I need to rebuild the fastinodelookuptable. let's do this!
  _rebuild_fastinodelookuptable()



# I'm already added.
def _recursive_rebuild_fastinodelookuptable_helper(path, inode):
  
  # for each entry in my table...
  for entryname,entryinode in filesystemmetadata['inodetable'][inode]['filename_to_inode_dict'].iteritems():
    
    # if it's . or .. skip it.
    if entryname == '.' or entryname == '..':
      continue

    # always add it...
    entrypurepathname = _get_absolute_path(path+'/'+entryname)
    fastinodelookuptable[entrypurepathname] = entryinode

    # and recurse if a directory...
    if 'filename_to_inode_dict' in filesystemmetadata['inodetable'][entryinode]:
      _recursive_rebuild_fastinodelookuptable_helper(entrypurepathname,entryinode)
    


def _rebuild_fastinodelookuptable():
  # first, empty it...
  for item in fastinodelookuptable:
    del fastinodelookuptable[item]

  # now let's go through and add items...
  
  # I need to add the root.   
  fastinodelookuptable['/'] = ROOTDIRECTORYINODE
  # let's recursively do the rest...
  
  _recursive_rebuild_fastinodelookuptable_helper('/', ROOTDIRECTORYINODE)