#!/usr/bin/env python

import time
from sqlog_logic import SQLog
from multiprocessing import Process
from sqlog_collector import SQLogCollector 

def start_collector():

    collector = SQLogCollector()

    try:
        thd = Process(target=collector.parser)
        res = thd.start()
        if thd.is_alive():
            return thd 
        return False
    except Exception as e:
        print "Could not start collector daemon. Reason: %s" % e 

def stop_collector(thd):
    try:
        """ Always return None, but lets check it anyway. """
        if thd.terminate() == None:
            while thd.is_alive():
                continue
            return True
    except Exception as e:
        print "Could not stop collector daemon. Reason: %s" % e

def check_fork():

    logic = SQLog()

    """ Check for fork type 3. If found, rebuild the blockchain."""
    if logic.check_fork3() and not logic.syncing() and not logic.get_rebuild_status() \
        and logic.blockchain_loaded():
        print "Fork type 3 detected, rebuilding..."
        if logic.set_rebuild_status("True"):
            if logic.rebuild():
                print "Rebuilt blockchain."
                return True
    return False

def check_height():

    logic = SQLog()
    c_height = logic.consensus_height()
    own_height = logic.own_height()

    if c_height and own_height:
        """ 1. Check if blockchain height is too low.
            2. Check that there is not on going rebuild.
            3. Check that the blockchain is not syncing. If its not syncing, we can do a rebuild.
        """
        if logic.height_low(c_height, own_height) and not logic.get_rebuild_status() \
            and not logic.syncing():
            """ Set rebuild status to True since we will do a rebuild. """
            if logic.set_rebuild_status("True"):
                print "Own (%s) blockheight is low compared to consensus(%s), rebuilding..." \
                    % (str(own_height), str(c_height))
                """ Activate forging on the other node. """
                if logic.failover():
                    """ If the failover/forging was set on the other node, rebuild. """
                    if logic.rebuild():
                        print "Rebuilt blockchain."
                        return True
    return False

def main():

    try:
        logic = SQLog()
        collector_thread = start_collector()

        if collector_thread:
            print "SQLog collector started."
            counter=0
            while True:

                """ Check for fork type 3. If found, rebuild the blockchain."""
                check_fork()

                """ Compare consensus blockchain height with own height. If out of sync rebuild. """
                if check_height():
                    """ The rebuild was successfull, set rebuild status to False in database """
                    logic.set_rebuild_status("False")

                if (counter % 1000) == 0:
                    if logic.stats():
                        print logic.stats()
                counter+=1
                time.sleep(3)
                    
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            print "SQLog collector stopped."

if __name__ == "__main__":
    main()
