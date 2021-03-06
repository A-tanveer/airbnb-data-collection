#!/usr/bin/python3
# ============================================================================
# Airbnb Configuration module, for use in web scraping and analytics
# ============================================================================
import logging
import psycopg2
import psycopg2.errorcodes
import os
import configparser
import sys
from datetime import datetime

logger = logging.getLogger()

class ABConfig():

    def __init__(self, args):
        """ Read the configuration file <username>.config to set up the run
        """
        self.config_file=args.config_file
        self.connection = None
        self.FLAGS_ADD = 1
        self.FLAGS_PRINT = 9
        self.FLAGS_INSERT_REPLACE = True
        self.FLAGS_INSERT_NO_REPLACE = False
        self.URL_ROOT = "http://www.airbnb.com/"
        self.URL_ROOM_ROOT = self.URL_ROOT + "rooms/"
        self.URL_HOST_ROOT = self.URL_ROOT + "users/show/"
        self.URL_SEARCH_ROOT = self.URL_ROOT + "s/"
        self.URL_API_SEARCH_ROOT = self.URL_ROOT + "search/search_results"
        self.SEARCH_AREA_GLOBAL = "UNKNOWN"  # special case: sample listings globally
        self.SEARCH_RECTANGLE_EDGE_BLUR = 0.1
        self.SEARCH_BY_NEIGHBORHOOD = 'neighborhood'  # default
        self.SEARCH_BY_ZIPCODE = 'zipcode'
        self.SEARCH_BY_BOUNDING_BOX = 'bounding box'
        self.SEARCH_LISTINGS_ON_FULL_PAGE = 18

        try:
            config = configparser.ConfigParser()

            if self.config_file is None:
                # look for username.config on both Windows (USERNAME) and Linux (USER)
                if os.name == "nt":
                    username = os.environ['USERNAME']
                else:
                    username = os.environ['USER']
                self.config_file = username + ".config"
            logger.info("Reading configuration file " + self.config_file)
            if not os.path.isfile(self.config_file):
                logger.error("Configuration file " + self.config_file + " not found.")
                sys.exit()
            config.read(self.config_file)

            # database
            try:
                self.DB_HOST = config["DATABASE"]["db_host"] if ("db_host" in config["DATABASE"]) else None
                self.DB_PORT = config["DATABASE"]["db_port"]
                self.DB_NAME = config["DATABASE"]["db_name"]
                self.DB_USER = config["DATABASE"]["db_user"]
                self.DB_PASSWORD = config["DATABASE"]["db_password"]
            except Exception:
                logger.error("Incomplete database information in " + config_file + ": cannot continue.")
                sys.exit()
            # network
            try:
                self.HTTP_PROXY_LIST = config["NETWORK"]["proxy_list"].split(",")
                self.HTTP_PROXY_LIST = [x.strip() for x in self.HTTP_PROXY_LIST]
            except Exception:
                logger.warning("No proxy_list in " + config_file + ": not using proxies")
                self.HTTP_PROXY_LIST = []
            try:
                self.USER_AGENT_LIST = config["NETWORK"]["user_agent_list"].split(",,")
                self.USER_AGENT_LIST = [x.strip() for x in self.USER_AGENT_LIST]
                self.USER_AGENT_LIST = [x.strip('"') for x in self.USER_AGENT_LIST]
            except Exception:
                logger.info("No user agent list in " + username +
                             ".config: not using user agents")
                self.USER_AGENT_LIST = []
            self.MAX_CONNECTION_ATTEMPTS = \
                int(config["NETWORK"]["max_connection_attempts"])
            self.REQUEST_SLEEP = float(config["NETWORK"]["request_sleep"])
            self.HTTP_TIMEOUT = float(config["NETWORK"]["http_timeout"])

            # survey
            self.FILL_MAX_ROOM_COUNT = int(config["SURVEY"]["fill_max_room_count"])
            self.ROOM_ID_UPPER_BOUND = int(config["SURVEY"]["room_id_upper_bound"])
            self.SEARCH_MAX_PAGES = int(config["SURVEY"]["search_max_pages"])
            self.SEARCH_MAX_GUESTS = int(config["SURVEY"]["search_max_guests"])
            self.SEARCH_MAX_RECTANGLE_ZOOM = int(
                config["SURVEY"]["search_max_rectangle_zoom"])
            self.RE_INIT_SLEEP_TIME = float(config["SURVEY"]["re_init_sleep_time"])

        except Exception:
            logger.exception("Failed to read config file properly")
            raise

    # get a database connection
    def connect(self):
        """ Return a connection to the database"""
        try:
            if (not hasattr(self, "connection") or
                self.connection is None or self.connection.closed != 0):
                cattr = dict(
                    user=self.DB_USER,
                    password=self.DB_PASSWORD,
                    database=self.DB_NAME
                )
                if self.DB_HOST is not None:
                    cattr.update(dict(
                                host=self.DB_HOST,
                                port=self.DB_PORT,
                                ))
                self.connection = psycopg2.connect(**cattr)
                self.connection.set_client_encoding('UTF8')
            return self.connection
        except psycopg2.OperationalError as pgoe:
            logger.error(pgoe.message)
            raise
        except Exception:
            logger.error("Failed to connect to database.")
            raise
