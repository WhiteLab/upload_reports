#!/usr/bin/env python
"""
Plugin/cronjob to sync project-specific sequencing info between bionimbus web and variant viewer

Usage: ./bionimbus_web-variant_viewer_sync.py <config>

Arguments:
    <config>    json config file with genome, caller, and get/post urls

Options:
    -h
"""

import json
import sys
import requests
import psycopg2
import pdb
from docopt import docopt


def set_web_stuff(client, url):
    # set verify to False if testing
    client.get(url, verify=False)
    return client.cookies['csrftoken'], dict(client.cookies), {"X-CSRFToken": client.cookies['csrftoken'],
                                                               "Referer": url}


def db_connect(database, username, password, host):
    try:
        constring = "dbname=" + database + " user=" + username + " password=" + password + " host=" + host
        return psycopg2.connect(constring)
    except:
        sys.stderr.write('Failed connection\n')
        exit(1)


def sync_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, username, password, get_status_url, db_user, db_pw, db_host, database, set_status_url) = \
        (config_data['login_url'], config_data['username'], config_data['password'], config_data['urlGetStatus'],
         config_data['dbUser'], config_data['dbPw'], config_data['dbHost'], config_data['db'],
         config_data['setStatusUrl'])

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)
    # get list of bnids to check bionimbus web for
    if r.status_code == 200:
        sys.stderr.write('Successfully logged in\n')
    else:
        sys.stderr.write('Login failed for url ' + login_url + '\n got error code ' + str(r.status_code) + '\n')
    status_info = post_client.get(get_status_url, params=login_data)
    pdb.set_trace()
    hold = 'horses'



def main():
    sync_status()


if __name__ == '__main__':
    main()