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
import json

from logging.handlers import RotatingFileHandler

def prepareLoggin(config):
    # TO-DO prepare loggin from config file/ cmd line args
    FORMAT_FILE = '%(asctime)-15s %(levelname)s %(message)s'
    FORMAT_CONSOLE = '%(levelname)s %(message)s'

    rootLogger = logging.getLogger()

    # file handler
    fileHandler = RotatingFileHandler('/tmp/dns_update.log', maxBytes=30*1024, backupCount=2)
    fileHandler.setFormatter(logging.Formatter(FORMAT_FILE))
    fileHandler.setLevel(logging.WARN)
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

def get_current_external_ip():

    url = 'https://api.ipify.org'
    connect_timeout=2
    read_timeout=2
    try:
        response = requests.request("GET", url, timeout=(connect_timeout,read_timeout))
        return response.text
    except requests.exceptions.RequestException as identifier:
        logging.log(logging.ERROR, 'Error getting current external IP')
        logging.log(logging.ERROR, identifier)
        return 'ERROR'

def update_ip(config, current_ip):

    sum_error = 0
    if 'services' in config:
        for service in config['services']:
            if not 'name' in service:
                logging.log(logging.WARN, 'Each service MUST have a name in order to work')
                continue
            else:
                if service['name'] == 'now-dns':
                    if all (key in service for key in ('name','hosts','user','pass')):
                        for host in service['hosts']:
                            sum_error += update_ip_now_dns(host,service['user'],service['pass'])
                    else:
                        logging.log(logging.ERROR, 'Each now-dns service MUST contains a valid service name in "name"; a valid user in "user"; a valid pass in "pass" and a list with the hostnames in "hosts"')
                        continue
                elif service['name'] == 'dynu':
                    if all (key in service for key in ('name','api_key')):
                        sum_error += update_ip_dynu(service['api_key'],current_ip)
                    else:
                        logging.log(logging.ERROR, 'Each dynu service MUST contains a valid service name in "name"; a valid api_key in "api_key"')
                        continue
                else:
                    logging.log(logging.WARN, 'Service ' + service['name'] + ' not supported')
    else:
        logging.log(logging.ERROR, 'the config file has no section "services"')
        return 1

    return sum_error

def update_ip_dynu(api_key, current_ip):

    domains_json = get_dynu_domains(api_key)

    all_domains_status = 0

    if 'domains' in domains_json:
        for domain in domains_json['domains']:

            if current_ip == domain['ipv4Address']:
                logging.log(logging.INFO, 'Servive: dynu.com; Domain: ' + domain['name'] + ' -> current IP (' + current_ip + ') not changed. Nothing to do.')
                continue

            logging.log(logging.WARN, 'Servive: dynu.com; Domain: ' + domain['name'] + ' -> updating the current external IP from ' + domain['ipv4Address'] + ' to ' + current_ip)

            url = "https://api.dynu.com/v2/dns/" + str(domain['id'])

            payload = {
                "Name": domain['name'],
                "Location" : "pikapi3",
                "ipv4Address": current_ip
            }
            headers = {
                'accept': 'application/json',
                'API-Key': api_key
            }

            connect_timeout=5
            read_timeout=5
            try:
                response = requests.request("POST", url, headers=headers, data = json.dumps(payload), timeout=(connect_timeout,read_timeout))
                if response.status_code == 200:
                    logging.log(logging.WARN,  "        Ip successfully updated")
                else:
                    logging.log(logging.ERROR, '        Status code: ' + str(response.status_code) + '; reason: ' + response.text)
                    all_domains_status += 1

            except requests.exceptions.RequestException as identifier:
                logging.log(logging.ERROR, identifier)
                all_domains_status += 1

    return all_domains_status

def get_dynu_domains(api_key):
    url = "https://api.dynu.com/v2/dns"

    payload = {}
    headers = {
        'accept': 'application/json',
        'API-Key': api_key
    }

    connect_timeout=5
    read_timeout=5
    try:
        response = requests.request("GET", url, headers=headers, data = payload, timeout=(connect_timeout,read_timeout))
    except requests.exceptions.RequestException as identifier:
        logging.log(logging.ERROR, "Error geting domains in dynu: ")
        logging.log(logging.ERROR, identifier)
        return {}

    if response.status_code == 200:
        return response.json()
    else:
        logging.log(logging.ERROR, "Error geting domains in dynu. Status code: " + str(response.status_code) + " return an empty json")
        return {}


def update_ip_now_dns(hostname, user, password):

    url = "https://now-dns.com/update?hostname=" + hostname

    payload = {}
    headers = {}

    connect_timeout=5
    read_timeout=5
    try:
        response = requests.request("GET", url, headers=headers, data = payload, auth=(user, password), timeout=(connect_timeout,read_timeout))
    except requests.exceptions.RequestException as identifier:
        logging.log(logging.ERROR, identifier)
        return 1

    if response.text == 'good':
        logging.log(logging.WARN, 'Servive: Now-DNS; hostname: ' + hostname + ': New IP successfully updated. Code: ' + response.text)
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
    current_ip = get_current_external_ip()
    status = update_ip(config_read, current_ip)
    if status > 0:
        logging.log(logging.ERROR, 'Current external IP: ' + current_ip + ' Something went wrong :-(')
    else:
        logging.log(logging.INFO, 'Current external IP: ' + current_ip + ' All OK :-)')

    exit(status)