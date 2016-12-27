## LISK/SHIFT monitoring software (Only LISK right now).

SQLog works as a monitoring software for LISK/SHIFT with a failover system. It also parse logs and inserts them into a SQLite3 database, hence the name SQLog. Since it uses a SQL-database as backend, it is very easy to create new events and actions.

## Supported events

SQLog enables high availability for LISK/SHIFT nodes. It can handle the following events.

| Event       | Action          |
| ------------- |:-------------:|
| Local node software is not running. | Try to start the local node software.|
| The node blockheight is low compared to network consensus | Failover and rebuild. Sends email if enabled.|
| The node experienced a fork of type 3 | Failover and rebuild. Sends email if enabled.|
|Broadhash consensus is either higher or lower than primary/secondary node|Failover|
|The blockchain database is corrupted|Failover and rebuild. Sends email if enabled.|

## Installation

1. `git clone https://github.com/shiftcurrency/sqlog.git`

2. Install python requests by using either python pip or apt (on debian based systems such as ubuntu).
   `apt-get install python-requests` or `pip install requests`

3. `Configure config.ini` in the sqlog directory. The configuration file is documented. OBSERVE, make sure you choose one server to be primary and one server to be secondary.

4. Start the software (in screen or similar) by executing sqlog.py, such as: ./sqlog.py

5. Make sure you white list the primary/secondary node IP-address in config.json for LISK/SHIFT as well as 127.0.0.1 on BOTH nodes.

## Event examples


### Secondary or primary node is down.
[2016-12-27 10:29:06] [INFO] Primary node is DOWN (both API and ICMP), forcing forging on secondary node.

[2016-12-27 10:29:07] [INFO] Forging enabled on node: 108.61.171.146

### Fork type 3 detected (no wait for low blockheight, the rebuild is executed immediately.
[2016-12-27 10:39:04] [INFO] Fork type 3 detected, rebuilding blockchain.

[2016-12-27 10:39:05] [INFO] Notification E-mail sent.

######################################################################## 100,0%

[2016-12-27 10:40:07] [INFO] Blockchain rebuild finished.

[2016-12-27 10:40:27] [INFO] Blockchain is syncing...

[2016-12-27 10:57:05] [INFO] Primary node OK, taking over.

[2016-12-27 10:57:05] [INFO] Forging enabled on node: 45.76.5.66

[2016-12-27 10:57:05] [INFO] Forging disabled on node: 108.61.171.146

### Corrupted blockchain database. Rebuild is executed on multiple types of corruption.
[2016-12-27 11:00:06] [INFO] Faulty database detected, rebuilding blockchain.

[2016-12-27 11:00:06] [INFO] Forging enabled on node: 108.61.171.146

[2016-12-27 11:00:06] [INFO] Forging disabled on node: 45.76.5.66

[2016-12-27 11:00:07] [INFO] Notification E-mail sent.

######################################################################## 100,0%

[2016-12-27 11:01:07] [INFO] Blockchain rebuild finished.

### Blockchain height is low compared to the network consensus height.
[2016-12-27 11:05:14] [INFO] Own blockheight is 20 blocks low compared to consensus, rebuilding blockchain.

[2016-12-27 11:05:15] [INFO] Notification E-mail sent.

######################################################################## 100.0%

[2016-12-27 11:06:06] [INFO] Blockchain rebuild finished.

### Broadhash consensus check. Always choose the node with the highest consensus.
[2016-12-27 10:57:05] [INFO] Primary node OK, taking over.

[2016-12-27 10:57:05] [INFO] Forging enabled on node: 45.76.5.66

[2016-12-27 10:57:05] [INFO] Forging disabled on node: 108.61.171.146

[2016-12-27 10:58:24] [INFO] Broadhash consensus on secondary node is higher than on primary node. Commit failover.

[2016-12-27 10:58:24] [INFO] Forging enabled on node: 108.61.171.146

[2016-12-27 10:58:24] [INFO] Forging disabled on node: 45.76.5.66

## The End

If you like my work you can give my delegate a vote (joey on LISK) or give me a small contribution at 3791057246258751384L.

## License

    <SQLog, SHIFT/LISK monitoring system>
    Copyright (C) <2016>  <Joey (shiftcurrency@gmail.com)>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
