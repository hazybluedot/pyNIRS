import logging
import re
import numpy as np
import os
from itertools import product

logger = logging.getLogger(__name__)

def key_tuple(l):
    key, val = l.split(':')
    return (key, int(val))

def parse_sdkey(val):
    return dict([ key_tuple(i) for i in val.strip(',').split(',') ])
    #return val

def parse_event(val):
    time, idx, something = val
    return time, int(idx), int(something)

TYPES = {
    'Gains': np.array,
    'S-D-Key': parse_sdkey,
    'S-D-Mask': lambda x: np.array(x, dtype=int),
    'Events': lambda x: [ parse_event(v) for v in x ]
}

header_re = re.compile(r'^\[([^\[\]]*)\]\s*$')
key_value_re = re.compile(r'^([-_a-zA-Z]+[0-9]*)=("?[^"#]*"?)\s*$')
start_multi_re = re.compile(r'^([-_a-zA-Z]+[0-9]*)="#\s*$')
end_multi_re = re.compile(r'^#"\s*$')
tablist_re = re.compile(r'"?([0-9\t.]+)"?$')

def marshal_value(val):
    m = tablist_re.match(val)
    if m:
        return [ float(v) for v in m.group(1).split() ]
    else:
        return val.strip('"')
    
def cfg_marshal(val):
    if val.startswith('"'):
        return marshal_value(val)
    else:
        try:
            return int(val)
        except ValueError:
            return float(val)
    
config_map = {
    header_re: lambda m, context: ('HEADER', m.group(1)),
    key_value_re: lambda m, context: ( 'ITEM', (m.group(1), cfg_marshal(m.group(2))) ),
    start_multi_re: lambda m, context: ( 'NEW_CONTEXT', m.group(1) )
}

def config_reader(f):
    context = None
    for line in f:
        if context is not None:
            m = end_multi_re.match(line)
            if m:
                logger.debug('reached end of multiline value')
                yield ('ITEM', (context['key'], context['buffer']))
                context = None
            else:
                context['buffer'].append(marshal_value(line.strip()))
        for regex, fn in config_map.items():
            m = regex.match(line)
            if m:
                item = fn(m, context)
                if item[0] in ['HEADER', 'ITEM']:
                    yield item
                if item[0] == 'NEW_CONTEXT':
                    context = { 'key': item[1], 'buffer': [] }
                
    logger.debug('config reader done'.format(line))

def marshal(key, value, types):
    try:
        return (key, types[key](value))
    except KeyError:
        return (key, value)
    
class DataLoader(object):
    def __init__(self, loader):
        self.is_loaded = False
        self.loader = loader
        self.data = None
        
    def __call__(self):
        if not self.is_loaded:
            self.data = self.loader()
            
        return self.data

    
class Config(object):
    def __init__(self, fname):
        self._dict = {}
        self.from_file(fname)
        self._wl_data = DataLoader(self._load_wldata)
        
    def from_file(self, fname):
        self.basedir, self.fname = os.path.split(fname) 
        with open(fname, 'r+') as f:
            config = {}
            header = None
            for action, payload in config_reader(f):
                logger.debug("{0}: {1}".format(action, payload))
                if action == 'HEADER':
                    header = payload
                    config[header] = {}
                if action == 'ITEM' and header is not None:
                    key, value = marshal(payload[0], payload[1], TYPES)
                    config[header][key] = value 
            self._dict = config

    def get(self, *args):
        if len(args) == 2:
            section, key = args
            return self._dict[section][key]
        else:
            raise Exception("find any key not implemented yet")

    def get_data_path(key):
        return make_path(self, self._dict[key])

    def file_ext(self, ext):
        return os.path.join(self.basedir, '{0}.{1}'.format(self.get('GeneralInfo', 'FileName'), ext))

    def _load_wldata(self):
        nWavelengths = len(self.wavelengths)
        return tuple([ np.genfromtxt(self.file_ext(e))[:,self.goodSDIdxs] for e in [ 'wl{0}'.format(i+1) for i in range(nWavelengths) ] ])
        
    @property
    def wl_data(self):
        return self._wl_data()
    
    def __str__(self):
        return str(self._dict)

    @property
    def wavelengths(self):
        return self.get('ImagingParameters', 'Wavelengths')
    
    @property
    def goodSDIdxs(self):
        """Return a list of indexes to valid source-detector combinations. Used to sift out valid data from useless data in the raw data files"""
        SDMask = self.get('DataStructure', 'S-D-Mask')
        SDKey = self.get('DataStructure', 'S-D-Key')
        M, N = SDMask.shape
        # Python indexes start from 0, hence the -1 below
        return [ SDKey["{0}-{1}".format(i+1, j+1)] - 1 for i,j in product(range(M), range(N)) if SDMask[i,j] == 1 ]

    def section(self, section):
        def _wrapped(key):
            return self.get(section,key)
        return _wrapped

if __name__ == '__main__':
    import sys
    from itertools import product 
    logging.basicConfig(level=logging.ERROR)

    # test config reader, provide a path to config file as first argument
    config = {}
    fname = sys.argv[1]
    cfg = Config(fname)

    print(cfg)
