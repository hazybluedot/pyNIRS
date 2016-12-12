# convert NIRx data to .nirs for use with HOMER2

import argparse
import logging
import numpy as np
import os

from itertools import product
from scipy.io import savemat

from pyNIRS.config import Config

logger = logging.getLogger(__name__)

def decode_SDtpl(val):
    try:
        iSrc, _zero, iDet = [ int(i) for i in str(int(val)) ]
    except ValueError:
        iSrc, iDet = None, None
    return iSrc, iDet

def SDpos(SD, config):
    """Generate source-detector position data. Warning: it has been
confirmed that this algorithm is *not* correct. Do not use position
information in analysis until this has been fixed."""
    tpl = config.load_by_ext('tpl')
    M, N = tpl.shape
    logger.debug('tpl shape: ({0}, {1})'.format(M, N))
    logger.warn('Position data is not correct. Do not use position data for analysis!')
    dChan = config.get('ChannelsDistance', 'ChanDis')
    xd, yd = dChan[0], dChan[1] # TODO: are these really always going to be the same? distance from what?
    nSrcs, nDets = SD['nSrcs'], SD['nDets']
    SD['SrcPos'] = np.zeros( (nSrcs, 3) ) 
    SD['DetPos'] = np.zeros( (nDets, 3) ) 

    zIdx = (N-1)/2
    for (i,j) in product(range(M), range(N)):
        iSrc, iDet = decode_SDtpl(tpl[i,j])
        if iSrc is not None and iDet is not None:
            logger.debug('Position for Src,Det {0} at {1}'.format((iSrc, iDet), (i,j)))
            xpos, ypos = (j - zIdx)*xd, (i+1)*yd
            SD['SrcPos'][iSrc - 1, :] = [ xpos, ypos, 0 ]
            SD['DetPos'][iDet - 1, :] = [ xpos, ypos, 0 ]

    return SD

def SDmeasList(config):
    nWavelengths = len(config.wavelengths)
    SDMask = config.get('DataStructure', 'S-D-Mask')
    SDKey = config.get('DataStructure', 'S-D-Key')
    M, N = SDMask.shape
    # third column is all ones by default... I have no idea what it is, just copying behavior from original script
    idexes = np.vstack( np.array((i+1, j+1, 1)) for i,j in product(range(M), range(N)) if SDMask[i,j] == 1 )
    nChannels = idexes.shape[0]
    logger.debug('measurement list has {0} channels'.format(nChannels))
                   
    return np.vstack( np.hstack( (idexes, (i+1)*np.ones(nChannels).reshape(nChannels,1) ) ) for i in range(nWavelengths) ) 

def s_events(config, N):
    events = config.get('Markers', 'Events')
    logger.debug("events: {0}".format(events))
    markerTypes = sorted(set([ e[1] for e in events]))
    nMarkerTypes = len(markerTypes)
    
    # load event file, this is the file with .evt extension in the data directory
    #event = np.genfromtxt(config.file_ext('evt'))
    # I think all the info re events we need is in the hdr file, so we don't need to load the .evt file. Am I mistaken?
    def eventIndexes(events, markerType):
        return [ e[2] for e in events if e[1] == markerType]
    def s_forMarkerType(events, markerType):
        return [ int(i in eventIndexes(events, 1)) for i in range(N) ]
    s = np.vstack( s_forMarkerType(events, t) for t in markerTypes ).transpose()
    logger.debug("s.shape: {0}".format(s.shape))
    return s

def cli():
    parser = argparse.ArgumentParser(description="a utility to convert the raw data from the NIRx machine to a .nirs format that can be used by HOMER2")
    
    parser.add_argument("config", type=Config, help="Config file (usually with extension .hdr) from the NIRx data directory")
    parser.add_argument("-v", "--verbose", action='store_true', help="Show informative output")
    parser.add_argument("-o", "--output", help="Output location or file. Defaults to a .nirs file in the same directory the config file was loaded from. Existing files with the same name will be overwritten.")
    parser.add_argument("-u", "--units", default='mm', choices=['mm', 'cm'], help='Spatial units for source-detector positions. Defaults to mm')
    
    args = parser.parse_args()
    config = args.config
    
    iparams = config.section('ImagingParameters')

    SD = {
        'Lambda': iparams('Wavelengths'),
        'nSrcs': iparams('Sources'),
        'nDets': iparams('Detectors'),
        'MeasList': SDmeasList(config),
        'SpatialUnit': args.units # don't see this anywhere in raw data, is it always 'mm' for NIRx?
    }
    SDpos(SD, config)
    
    logger.debug('SD = {0}'.format(SD))
    
    # load wavelength files
    wl_data = config.wl_data
    if args.verbose:
        if len(wl_data) != len(config.wavelengths):
            logger.warn("Loaded {0} wavelenght files but found {1} wavelengths listed in the configuration".format(len(wl_data), len(config.wavelengths)))
        else:
            print("loaded {0} wavelength files".format(len(wl_data)))

    d = np.hstack(wl_data)
    N = d.shape[0]
    
    # time is a linearly spaced vector same length as the number of rows of wl1 (or wl2), wl1.shape[0]
    fs = iparams('SamplingRate')
    Ts = 1/fs
    t = np.arange(0, N*Ts, Ts).reshape(N,1)

    s = s_events(config, N)

    # not sure what aux is used for, Taiwan script had it as a Nx1
    # vector same length as data, nirx2nirs had it as a Nx8 matrix. N
    # = number of data rows
    aux = np.zeros( (N,1) )

    outfile = config.file_ext('nirs')
    if args.output:
        path, ofname = os.path.split(outfile)
        if os.path.isdir(args.output):
            outfile = os.path.join(args.output, ofname)
        else:
            outfile = args.output

    # A .nirs file is actually just a MATLAB data file (usually .mat)
    savemat(outfile, { 'd': d, 's': s, 't': t, 'aux': aux, 'SD': SD }, appendmat=False)
    if args.verbose:
        print("wrote matfile to {0}".format(outfile))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    cli()
