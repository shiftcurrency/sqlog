## LISK/SHIFT monitoring software.

SQLog works as a monitoring software for LISK/SHIFT with a failover system. It also parse logs and inserts them into a SQLite3 database, hence the name SQLog.

## Supported events

SQLog enables high availability for LISK/SHIFT nodes. It can handle the following events.

- Event: Local node software is not running.
  Action: Try to start the local node software.
- Event: The node blockheight is low compared to network consensus (the block offset can be configured).
  Action: Failover and rebuild.
- Event: The node experienced a fork of type 3.
  Action: Failover and rebuild.
- Event: Broadhash consensus is either higher or lower than primary/secondary node.
  Action: Failover.
- Event: The blockchain database is corrupted and does a rebuild from block 0 (this takes a lot of time, much faster to do a rebuild).
  Action: Failover and rebuild.

## Installation

1. git clone https://github.com/shiftcurrency/sqlog.git

2. Install python requests by using either python pip or apt (on debian based systems such as ubuntu).
   apt-get install python-requests or pip install requests

3. Configure config.ini in the sqlog directory. The configuration file is documented. OBSERVE, make sure you choose one server to be primary and one server to be secondary.

4. Start the software (in screen or similar) by executing sqlog.py, such as: ./sqlog.py

## License

A short snippet describing the license (MIT, Apache, etc.)
