#!/usr/bin/env python

import time
import sys
import ConfigParser
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

def low_broadhash():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.check_broadhash() == "secondary" and not logic.syncing() and not logic.get_rebuild_status() \
        and logic.blockchain_loaded() and not logic.forging(config.get("failover", "secondary_node")):
        if config.get("failover", "this_node") == "primary":
            logic.logger("Broadhash under 51%, commit failover.")
            if logic.failover("secondary"):
                return True
    return False

def primary_takeover():

    """ Always make sure that the primary node is active if everything is OK. """
    if not logic.syncing() and not logic.get_rebuild_status() and logic.blockchain_loaded() \
        and logic.check_broadhash() == "primary" and not logic.check_fork3() and not logic.height_low() \
        and not logic.forging(config.get("failover", "primary_node")):
        """ Everything is OK at primary node. """
        if config.get("failover", "this_node") == "primary":
            if logic.failover("primary"):
                return True
    return False

def bad_db_rebuild():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.bad_memory_table() and not logic.syncing() and not logic.get_rebuild_status() and logic.blockchain_loaded():
        """ 1. Set rebuild status to True
            2. Commit a fail over. """
        if logic.set_rebuild_status("True") and logic.failover("secondary"):
            logic.logger("Faulty database detected, rebuilding blockchain.")
            if logic.run_script("rebuild"):
                logic.logger("Blockchain rebuild finished.")
                if logic.syncing():
                    logic.logger("Syncing blockchain.")
                return True
    return False


def check_fork():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.check_fork3() and not logic.syncing() and not logic.get_rebuild_status() and logic.blockchain_loaded() \
        and not logic.forging(config.get("failover", "secondary_node")):
        """ 1. Set rebuild status to True
            2. Commit a fail over. """
        if logic.set_rebuild_status("True"):
            if config.get("failover", "this_node") == "primary":
                logic.failover("secondary")
            logic.logger("Fork type 3 detected, rebuilding blockchain.")
            if logic.run_script("rebuild"):
                logic.logger("Blockchain rebuild finished.")
                if logic.syncing():
                    logic.logger("Syncing blockchain.")
                return True
    return False

def check_height():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.height_low() and not logic.syncing() and not logic.get_rebuild_status() and logic.blockchain_loaded():
        """ 1. Set rebuild status to True
            2. Commit a fail over. """
        if not logic.forging(config.get("failover", "secondary_node")):
            if config.get("failover", "this_node") == "primary":
                logic.failover("secondary")
            if logic.set_rebuild_status("True"):
                log = "Own blockheight is %s blocks low compared to consensus, rebuilding blockchain." \
                    % (str(config.get("general", "block_offset")))
                logic.logger(log)
                if logic.run_script("rebuild"):
                    logic.logger("Blockchain rebuild finished.")
                    if logic.syncing():
                        logic.logger("Syncing blockchain.")
                    return True
    return False

def main():
    try:
        counter=0
        collector_thread = start_collector()
        if collector_thread:
            logic.logger("SQLog collector started.")
            if not logic.syncing(): logic.stats()
            while True:
                counter+=1
                if (counter % 300) == 0:
                    if not logic.syncing(): logic.stats()
                if check_height():
                    logic.set_rebuild_status("False")
                if check_fork():
                    logic.set_rebuild_status("False")
                if low_broadhash():
                    """ No rebuild needed. We do not set rebuild status. Continue. """
                    continue
                if primary_takeover():
                    """ No rebuild needed. We do not set rebuild status. Continue. """
                    continue
                time.sleep(3)
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            logic.logger("SQLog collector stopped.")

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    try:
        config.read('config.ini')
    except Exception as e:
        print "Could read config.ini. Reason: %s" % e
        sys.exit(1)
    logic = SQLog()
    main()
