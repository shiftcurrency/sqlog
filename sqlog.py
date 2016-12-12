#!/usr/bin/env python

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

if __name__ == "__main__":
    try:
        collector_thread = start_collector()
        if collector_thread:
            print "SQLog collector started."
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            print "SQLog collector stopped."
