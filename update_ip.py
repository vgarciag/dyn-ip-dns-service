#!/usr/bin/env python
# -*- coding: utf-8 -*-

''' Script to update IP y NOW-DNS service

This script updates the IP into NOW-DNS service.

'''
import requests
import logging
import argparse
import configparser
import yaml

from logging.handlers import RotatingFileHandler

def prepareLoggin(config):
	# TO-DO prepare loggin from config file/ cmd line args
	FORMAT_FILE = '%(asctime)-15s %(levelname)s %(message)s'
	FORMAT_CONSOLE = '%(levelname)s %(message)s'

	rootLogger = logging.getLogger()

	# file handler
	fileHandler = RotatingFileHandler('/tmp/dns_update.log', maxBytes=30*1024, backupCount=2)
	fileHandler.setFormatter(logging.Formatter(FORMAT_FILE))
	rootLogger.addHandler(fileHandler)

	#console handler
	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(logging.Formatter(FORMAT_CONSOLE))
	rootLogger.addHandler(consoleHandler)

	rootLogger.setLevel(logging.INFO)

def load_config(config_file):
    try:
        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except OSError as exc: 
        print('ERROR opening file: ' + exc.strerror)
        exit(1)
    except yaml.YAMLError as exc_yaml:
        print(exc_yaml)
        exit(1)

def update_ip(config):

    sum_error = 0
    if 'services' in config:
        for service in config['services']:
            if all (key in service for key in ('name','hosts','user','pass')):
                if service['name'] == 'now-dns':
                    for host in service['hosts']:
                        sum_error += update_ip_now_dns(host,service['user'],service['pass'])
            else:
                logging.log(logging.ERROR, 'Each service MUST contains a valid service name in "name"; a valid user in "user" and a valid pass in "pass" and a list with the hostnames in "hosts"')
                return 1

    else:
        logging.log(logging.ERROR, 'the config file has no section "services"')
        return 1

    return sum_error

def update_ip_now_dns(hostname, user, password):

    url = "https://now-dns.com/update?hostname=" + hostname

    payload = {}
    headers = {}

    connect_timeout=5
    read_timeout=5
    response = requests.request("GET", url, headers=headers, data = payload, auth=(user, password), timeout=(connect_timeout,read_timeout) )

    if response.text == 'good':
        logging.log(logging.INFO, 'Servive: Now-DNS; hostname: ' + hostname + ': New IP successfully updated. Code: ' + response.text)
        return(0)
    elif response.text == 'nochg':
        logging.log(logging.INFO, 'Servive: Now-DNS; hostname: ' + hostname + ': No IP updated still the same. Code: ' + response.text)
        return(0)
    elif response.text == 'nohost':
        logging.log(logging.ERROR, 'Servive: Now-DNS; hostname: ' + hostname + 'No valid host ' + hostname + ' for user provided. Code: ' + response.text)
        return(1)
    elif response.text == 'notfqdn':
        logging.log(logging.ERROR, 'Servive: Now-DNS; hostname: ' + hostname + 'No a valid host ' + hostname + '  provided. Code: ' + response.text)
        return(2)
    elif response.text == 'badauth':
        logging.log(logging.ERROR, 'Servive: Now-DNS; hostname: ' + hostname + ': No valid credentials. Code: ' + response.text)
        return(3)
    else:
        logging.log(logging.WARN, 'Servive: Now-DNS; hostname: ' + hostname + 'Server returned not undertanding answer: ' + response.text)
        return(4)
        
def process_args():

  parser = argparse.ArgumentParser(description='Update current IP to several Dynami ip services')

  parser.add_argument('--config',
                      '-c',
                      dest='config_file',
                      action='store',
                      type=str,
                      required=True,
                      help='Config file path')


  return parser.parse_args()


if __name__ == "__main__":
    pargs = process_args()
    config_read = load_config(pargs.config_file)
    prepareLoggin(config_read)
    status = update_ip(config_read)
    if status > 0:
        logging.log(logging.ERROR, 'Something went wrong')
    else:
        logging.log(logging.INFO, 'All OK :-)')

    exit(status)