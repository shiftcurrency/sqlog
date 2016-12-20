import json
import requests
import subprocess
import sys
import os.path
import sqlite3
import ConfigParser
import logging
import logging.config
import re

class SQLog(object):

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.read('config.ini')
        except Exception as e:
            print "Could read config.ini. Reason: %s" % e 
            sys.exit(1)

    def logger(self, log_string):
        logging.config.dictConfig({"version":1, "disable_external_loggers":True})
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, \
                format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.info(log_string)
        
    def node_running(self, ip):
        
        """ Return values:
            True: Node is running.
            False: Node is not running. """
        url = "http://" + str(ip) + ":" + self.config.get("general", "api_port") + "/api/blocks/getFee"
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res:
                return True
        except Exception as e:
            return False
        return False

    def forging(self, ip):

        """ Argument: IP-address(string).
            Return values:
            True: IP-address with account is forging.
            False: IP-address with account is not forging.
            None: Exception thrown. """

        try:
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()
            self.c.execute('DELETE FROM status')
        except Exception as e:
            log = "Could not interact with status database. Reason: %s" % e
            self.logger(log)
            return None

        url = "http://" + ip + ":" + self.config.get("general", "api_port") + \
                "/api/accounts/getPublicKey?address=" + self.config.get("failover", "address")
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success'] == True and 'publicKey' in res:
                public_key = res['publicKey']
            else:
                return None
        except Exception as e:
            log = "Could not get public key of account %s. Reason: %s" % \
                (self.config.get("failover", "address"), e)
            self.logger(log)
            return None

        url = "http://" + ip + ":" + self.config.get("general", "api_port") + \
                "/api/delegates/forging/status?publicKey=" + public_key
        try:
            http_req = requests.get(url)
            res = http_req.json()

            if 'success' in res and res['success'] == True:
                if res['enabled'] == True:
                    if ip == self.config.get("failover", "primary_node"):
                        self.c.execute('INSERT INTO status (whos_forging) VALUES ("primary")')
                    elif ip == self.config.get("failover", "secondary_node"):
                        self.c.execute('INSERT INTO status (whos_forging) VALUES ("secondary")')
                    return True
        except Exception as e:
            log = "Could not get or check forging status of node %s for address %s. Reason: %s" % \
                (ip, self.config.get("failover", "address"), e)
            self.logger(log)
            return None
        return False

    def blockchain_loaded(self):

        """ 
        Return values: 
        True: The blockchain is loaded.
        False: The blockchain is not loaded.
        None: Exception, we can not determine if the blockchain is loaded.
        """
        
        url = "http://127.0.0.1:" + self.config.get("general", "api_port") + "/api/loader/status"
        try:
            http_req = requests.get(url)
            res = http_req.json()
        except Exception as e:
            log = "Could not fetch node status. Reason: %s" % e
            self.logger(log)
            return None

        if 'success' in res and res['success'] == True and 'loaded' in res and res['loaded'] == True:
            return True
        return False

    def get_rebuild_status(self):

        """ 
        Return values: 
        True: We have an on going blockchain rebuild.
        False: We do not have an on going blockchain rebuild.
        None: An exception as thrown. Can not determine a if we have an on going rebuild.
        """

        try:
            self.conn_db = self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()
            self.c.execute('SELECT rebuild FROM status')
            res = self.c.fetchall()
        except Exception as e:
            log = "Could not fetch rebuild status. Reason: %s" % e
            self.logger(log)
            return None

        if len(res) > 0:
            if res[0][0] == "True":
                return True
        return False

    def set_rebuild_status(self, status):

        """ 
        Return values: 
        True: Successfully updated the database that we have an on going rebuild.
        False: Could not update the database that we have an on going rebuild.
        """

        try:
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()
            self.c.execute('DELETE FROM status')
            sql = "INSERT INTO status (rebuild) VALUES (\'%s\');" % status
            self.c.execute(sql)
            self.conn_db.commit()
            self.conn_db.close()
        except Exception as e:
            log = "Could not set rebuild status to True. Reason: %s" % e
            self.logger(log)
            return False
        return True
 
    def consensus_height(self):

        """ 
        Return values: 
        Success: Blockheight as an integer
        False: No values could be fetched.
        """

        heights = []
        ips = self.config.get("general", "blockheight_nodes")

        for ip in ips.split():
            url = "http://" + str(ip) + ":" + self.config.get("general", "api_port") + "/api/blocks/getHeight"
            try:
                http_req = requests.get(url)
                res = http_req.json()
            except Exception as e:
                return None
            if 'success' in res and res['success'] and 'height' in res:
                heights.append(res['height'])

        if len(heights) > 0:
            heights.sort()
            return heights[-1]
            
        return False

    def height_low(self):
        
        own_height = self.own_height()
        consensus_height = self.consensus_height()

        if consensus_height and own_height and \
            (int(own_height+int(self.config.get("general", "block_offset")) <= int(consensus_height))):
            return True
        return False

    def syncing(self):

        """ Return values: 
            height: as integer on success
            None: if no result is returned
            False: Exception """

        url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/loader/status/sync'
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success']:
                if res['syncing'] == True:
                    return True
        except Exception as e:
            pass
        return False

    def own_height(self):

        """ Return values: 
            height: as integer on success
            False: if no result is returned
            None: Exception, could not fetch own blockheight. """

        url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/blocks/getHeight'
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success']:
                height = res['height']
                return height
        except Exception as e:
            return None
        return False

    def run_script(self, action):

        try:
            p = subprocess.Popen(["/bin/bash", str(self.config.get("paths", "management_script")), action],  stdout=subprocess.PIPE, shell=False)
            (output, err) = p.communicate()
            proc_status = p.wait()
            if proc_status == 0:
                return True
        except Exception as e:
            return None
        return False

    def check_broadhash(self):

        if self.config.get("failover", "primary_node") and self.config.get("failover", "secondary_node"):
            url = 'http://' + self.config.get("failover", "primary_node") + ":" + (self.config.get("general", "api_port")) \
                + '/api/loader/status/sync'
            try:
                http_req = requests.get(url)
                res = http_req.json()
                if 'success' in res and res['success'] == True and 'consensus' in res:
                    primary_broadhash_consensus = int(res['consensus'])
            except Exception as e:
                print e
                return None

            url = 'http://' + self.config.get("failover", "secondary_node") + ":" + (self.config.get("general", "api_port")) \
                + '/api/loader/status/sync'
            try:
                http_req = requests.get(url)
                res = http_req.json()
                if 'success' in res and res['success'] == True and 'consensus' in res:
                    secondary_broadhash_consensus = int(res['consensus'])
            except Exception as e:
                print e
                return None

            if (primary_broadhash_consensus < secondary_broadhash_consensus):
                return True
        return False


    def bad_memory_table(self):

        """ Return values:
            False: We did not find a bad memory table rebuild within the last 30 seconds.
            True: We found a bad memory table. """

        """ If LISK/SHIFT finds e.g. an orphaned block, the database has to be rebuild from block 0. This takes too long.
            We should therefore initiate a rebuild and do a failover instead. """

        """ Rebuilding blockchain, current block height: 1 """
        try:
            sql = 'SELECT * FROM logs WHERE log_string like \'%Rebuilding blockchain, current block height%\'' + \
                    'AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\', datetime(\'now\', \'-30 seconds\'))) < datetime ORDER BY datetime DESC LIMIT 1'
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
            self.c = self.conn_db.cursor()
            self.c.execute(sql)
            res = self.c.fetchall()
            if len(res) == 0:
                return False
        except Exception as e:
            log = "Could not do bad memory check. Reason: %s" % e
            self.logger(log)
            return None
        return True

    def failover(self, node):

        """ Argument: primary or secondary as string for which to enable forging on. """

        """ Return values:
            True: Disabled forging on primary node, enabled forging on secondary node.
            False: Could not disable forging on local node or enable forging on remote node.
            None: Exception thrown. """

        """ Check if this local node is acting as primary or secondary. """
        if node == 'primary':
            ip_active = self.config.get("failover", "primary_node")
            ip_inactive = self.config.get("failover", "secondary_node")
        elif node == 'secondary':
            ip_active = self.config.get("failover", "secondary_node")
            ip_inactive = self.config.get("failover", "primary_node")
            
        try:
            data = {"secret": str(self.config.get("failover", "secret"))}
            headers = {'Content-Type': 'application/json'}

            """ Enable forging on primary OR secondary node. If forging is already enabled, do it anyway just to be safe. """
            url = 'http://' + str(ip_active) + ':' + (self.config.get("general", "api_port")) + '/api/delegates/forging/enable'
            r = requests.post(url, data=json.dumps(data), headers=headers)
            res = r.json()

            if 'success' in res and res['success'] == True:
                log = "Forging enabled on node: %s" % str(ip_active)
                self.logger(log)

            url = 'http://' + str(ip_inactive) + ':' + (self.config.get("general", "api_port")) + '/api/delegates/forging/disable'
            r = requests.post(url, data=json.dumps(data), headers=headers)
            res = r.json()
            if 'success' in res and res['success'] == True:
                log = "Forging disabled on node: %s" % str(ip_inactive)
                self.logger(log)
        except Exception as e:
            log = "Could not commit failover. Reason: %s" % e
            self.logger(log)
            return None
        return True
        
    def check_fork3(self):

        """ Return values:
        False: No fork type 3 detected within the specific time frame. 
        True: There was a fork type 3 within the specific timeframe
        None: Exception, we can not determine if a fork type 3 occurred. """

        try:
            sql = 'SELECT * FROM logs WHERE log_string LIKE \'%Fork%\' AND log_string LIKE \'%"cause":3%\' AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\',' + \
                    'datetime(\'now\', \'-30 seconds\'))) < datetime'
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
            self.c = self.conn_db.cursor()
            self.c.execute(sql)
            if len(self.c.fetchall()) >= 1:
                return True
        except Exception as e:
            return None
        return False

    def stats(self):

        try:
            sql = 'SELECT COUNT(severity) FROM logs'
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
            self.c = self.conn_db.cursor()
            self.c.execute(sql)
            num_lines = self.c.fetchall()



            if len(num_lines) >= 1:
                if self.forging(self.config.get("failover", "primary_node")):
                    log = "Primary node(%s) is forging." % self.config.get("failover", "primary_node")
                    self.logger(log)
                elif self.forging(self.config.get("failover", "secondary_node")):
                    log = "Secondary node(%s) is forging." % self.config.get("failover", "secondary_node")
                    self.logger(log)
                own_height = self.own_height()
                con_height = self.consensus_height()
                if own_height and con_height:
                    log = 'Local blockchain height: %s; Consensus blockchain height: %s.' % (own_height, con_height)
                    self.logger(log)
                    log = 'Log lines parsed: %i' % num_lines[0]
                    self.logger(log)
        except Exception as e:
            self.logger("Could not fetch number of lines parsed for statistics.")
        return True
