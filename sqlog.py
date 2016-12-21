#!/usr/bin/env python

import time
import sys
import ConfigParser
from sqlog_logic import SQLog
from multiprocessing import Process
from sqlog_collector import SQLogCollector 
from sqlog_notifications import Email

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

def node_running(node):

    if node == "primary" and not logic.node_running(config.get("failover", "primary_node")):
        if config.get("notifications", "enable_email"):
            res = mail.send_email("Primary node is down.")
        return False
    elif node == "secondary" and not logic.node_running(config.get("failover", "secondary_node")):
       if config.get("notifications", "enable_email"):
            res = mail.send_email("Secondary node is down.")
            return False
    else:
        return True

def low_broadhash():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """

    if logic.check_broadhash() and config.get("failover", "this_node") == "primary" \
            and logic.forging(config.get("failover", "primary_node")):
        if logic.failover("secondary"):
            logic.logger("Broadhash consensus on secondary node is higher than on primary node. Commit failover.")
            return True
    return False

def primary_takeover():

    """ Always make sure that the primary node is active if everything is OK. """
    if not logic.check_broadhash() and not logic.syncing() and not logic.get_rebuild_status() and logic.blockchain_loaded() \
        and not logic.check_fork3() and not logic.height_low() \
        and not logic.forging(config.get("failover", "primary_node")):
        """ Everything is OK at primary node. """
        if config.get("failover", "this_node") == "primary":
            logic.logger("Primary node OK, taking over.")
            if logic.failover("primary"):
                return True
    return False

def bad_db_rebuild():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.bad_memory_table() and not logic.get_rebuild_status() and logic.set_rebuild_status("True"):
        if config.get("failover", "this_node") == "primary" and logic.forging(config.get("failover", "primary_node")):
            logic.failover("secondary")
        log = "Faulty database detected, rebuilding blockchain."
        logic.logger(log)
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
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
            log = "Fork type 3 detected, rebuilding blockchain."
            logic.logger(log)
            if config.get("notifications", "enable_email"):
                res = mail.send_email(log)
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
                if config.get("notifications", "enable_email"):
                    res = mail.send_email(log)
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
                time.sleep(15)
                if (counter % 300) == 0:
                    if not logic.syncing(): logic.stats()
                if not node_running(config.get("failover", "this_node")):
                    logic.logger("Node software on localhost is not running, trying to start it...")
                    if config.get("failover", "this_node") == "primary":
                        logic.failover("secondary")
                    if logic.run_script("start"):
                        logic.logger("Node started on localhost.")
                        continue
                else:
                    if check_height():
                        logic.set_rebuild_status("False")
                    if check_fork():
                        logic.set_rebuild_status("False")
                    if bad_db_rebuild():
                        logic.set_rebuild_status("False")
                    if low_broadhash():
                        """ No rebuild needed. We do not set rebuild status. Continue. """
                        continue
                    if primary_takeover():
                        """ No rebuild needed. We do not set rebuild status. Continue. """
                        continue
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            logic.logger("SQLog collector stopped.")

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    logic = SQLog()
    mail = Email()
    try:
        config.read('config.ini')
    except Exception as e:
        log = "Could read config.ini. Reason: %s" % e
        logic.logger(log)
        sys.exit(1)
    main()
