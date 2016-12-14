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
    if logic.check_fork3() and not logic.syncing() and not logic.get_rebuild_status():
        print "Fork type 3 detected, rebuilding..."
        if logic.set_rebuild_status("True"):
            if logic.rebuild():
                print "Rebuilt blockchain."
                logic.set_rebuild_status("False")
                return True
    return False

def check_height():

    logic = SQLog()
    c_height = logic.consensus_height()
    own_height = logic.own_height()
    if c_height and own_height:
        if logic.height_low(c_height, own_height) and not logic.syncing() \
                and not logic.get_rebuild_status():
            print "Own blockheight is low compared to consensus, rebuilding..."
            if logic.set_rebuild_status("True"):
                if logic.rebuild():
                    print "Rebuilt blockchain."
                    logic.set_rebuild_status("False")

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
                check_height()

                if (counter % 1000) == 0:
                    if logic.stats_lines_parsed(): print logic.stats_lines_parsed()
                counter+=1
                time.sleep(2)
                    
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            print "SQLog collector stopped."

if __name__ == "__main__":
    main()
