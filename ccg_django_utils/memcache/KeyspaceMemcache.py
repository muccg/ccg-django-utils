import memcache
from django.conf import settings
from pickle import Pickler, Unpickler

class KeyspacedMemcacheClient(memcache.Client):
    KEYSPACE = settings.MEMCACHE_KEYSPACE

    def __init__(self, servers=None, debug=0, pickleProtocol=0, pickler=Pickler, unpickler=Unpickler, pload=None, pid=None, keyspace=None):
        if servers==None:
            servers = settings.MEMCACHE_SERVERS
        if keyspace != None:
            self.KEYSPACE = keyspace
        memcache.Client.__init__(self,servers, debug, pickleProtocol, pickler, unpickler, pload, pid)


    def __del__(self):
        self.disconnect_all()

    def add(self, key, val, time=0, min_compress_len=0):
        return memcache.Client.add(self, self.KEYSPACE+key, val, time, min_compress_len)

    def append(self, key, val, time=0, min_compress_len=0):
        return memcache.Client.append(self, self.KEYSPACE+key, val, time, min_compress_len)

    def decr(self, key, delta=1):
        return memcache.Client.decr(self, self.KEYSPACE+key, delta)

    def delete(self, key, time=0):
        return memcache.Client.delete(self, self.KEYSPACE+key, time)

    def delete_multi(self, keys, time=0, key_prefix=''):
        return memcache.Client.delete_multi(self, keys, time, self.KEYSPACE+key_prefix)

    def get(self, key):
        return memcache.Client.get(self, self.KEYSPACE+key)

    def get_multi(self, keys, key_prefix=''):
        return memcache.Client.get_multi(self, keys, self.KEYSPACE+key_prefix)

    def incr(self, key, delta=1):
        return memcache.Client.incr(self, self.KEYSPACE+key, delta)

    def prepend(self, key, val, time=0, min_compress_len=0):
        return memcache.Client.prepend(self, self.KEYSPACE+key, val, time, min_compress_len)

    def replace(self, key, val, time=0, min_compress_len=0):
        return memcache.Client.replace(self, self.KEYSPACE+key, val, time, min_compress_len)

    def set(self, key, val, time=0, min_compress_len=0):
        return memcache.Client.set(self, self.KEYSPACE+key, val, time, min_compress_len)

    def set_multi(self, mapping, time=0, key_prefix='', min_compress_len=0):
        return memcache.Client.set_multi(self, mapping, time, self.KEYSPACE+key_prefix, min_compress_len)
