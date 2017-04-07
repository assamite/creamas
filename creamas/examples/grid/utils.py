'''
.. py:module:: utils
    :platform: Unix

Utility functions for the grid simulations.
'''
import logging
import os


def configure_logger(logger, filename, folder, log_level):
    '''Configure logging behvior for the simulations.
    '''
    fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    if folder is not None:
        log_file = os.path.join(folder, filename)
        hdl = logging.FileHandler(log_file)
        hdl.setFormatter(fmt)
        hdl.setLevel(log_level)
        logger.addHandler(hdl)
    shdl = logging.StreamHandler()
    shdl.setLevel(log_level)
    shdl.setFormatter(fmt)
    logger.addHandler(shdl)
    logger.setLevel(log_level)


def stop_managers(mgr_file):
    import aiomas
    import socket
    mgrs = []
    with open(mgr_file, 'r') as f:
        a = f.readlines()
        mgrs = [l.strip() for l in a]

    host = "{}.hpc.cs.helsinki.fi".format(socket.gethostname())
    c = aiomas.Container.create((host, 5600), codec=aiomas.MsgPack)
    closed = []
    for addr in mgrs:
        print("Trying to close {}".format(addr))
        try:
            ra = aiomas.run(c.connect(addr, timeout=2))
            ret = aiomas.run(ra.stop())
            print("Closed {}.".format(addr))
            closed.append(addr)
        except:
            print("Could not stop {}".format(addr))
    print("{}/{} closed".format(len(closed), len(mgrs)))
    c.shutdown()
