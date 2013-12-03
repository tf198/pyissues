'''
dirshelve.py, v0.1

Implements shelve API using files in a directory.
Supports path type keys e.g. 'subdir/testing'.
Implements smart writeback.

    import dirshelve
    
    data = dirshelve.open('data', writeback=True)
    
    data['test1'] = 'one'
    data['subdir/test2'] = 'two'
    
    assert(data['test1'] == 'one')
    
    data.sync()
    
    data.close()

'''

from collections import MutableMapping
import os, logging

fopen = __builtins__['open']

logger = logging.getLogger(__name__)

try:
    import cPickle as pickle
except ImportError:
    import pickle


def open(dirname, writeback=False):
    return DirShelf(dirname, writeback)

class DirShelf(MutableMapping):
    
    def __init__(self, dirname, writeback=False):
        self.dirname = os.path.realpath(dirname)
        
        self.writeback = writeback
        self._cache = {}
        self._initial = {}
        
        if not os.path.isdir(self.dirname):
            os.makedirs(self.dirname)
        
    def close(self):
        self.sync()
        self.dirname = None
        self._cache = None
        self._initial = None
        
    def sync(self):
        synced = []
        for name in self._initial:
            data = pickle.dumps(self._cache[name])
            if hash(data) != self._initial[name]:
                logger.debug("Syncing '{0}'".format(name))
                with fopen(self._key_path(name), 'wb') as f:
                    f.write(data)
                synced.append(name)
        self._initial = {}
        return synced
    
    def _key_path(self, name):
        path = os.path.join(self.dirname, name)
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass
        return path
    
    def _load_item(self, name):
        try:
            with fopen(self._key_path(name), 'rb') as f:
                data = f.read()
        except IOError:
            raise KeyError(name)
        
        if self.writeback:
            self._initial[name] = hash(data)
        
        return pickle.loads(data)
        
    def _save_item(self, name, value):
        pickle.dump(value, fopen(self._key_path(name), 'wb'))
        if name in self._initial:
            del(self._initial[name])
    
    def __getitem__(self, name):
        if self.dirname is None:
            raise ValueError("Shelf is closed")
    
        if not name in self._cache:
            self._cache[name] = self._load_item(name)
        return self._cache[name]
        
    def __setitem__(self, name, value):
        if self.dirname is None:
            raise ValueError("Shelf is closed")
    
        self._cache[name] = value
        if self.writeback:
            self._initial[name] = None
        else:
            self._save_item(name, value)
            
    def __delitem__(self, name):
        try:
            os.unlink(self._key_path(name))
        except OSError:
            if not (self.writeback and name in self._cache):
                raise KeyError(name)
    
        if name in self._cache:
            del(self._cache[name])
            
        if name in self._initial:
            del(self._initial[name])

    def _keys(self):
        keys = set(self._cache.keys())
        
        c = len(self.dirname) + 1
        for root, dirs, files in os.walk(self.dirname):
            keys.update([ os.path.join(root[c:], x) for x in files ])
            
        return keys

    def __iter__(self):
        return iter(self._keys())
        
    def __len__(self):
        return len(self._keys())
