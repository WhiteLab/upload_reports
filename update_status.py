#!/usr/bin/env python
"""
Plugin to interface with variant viewer - update sequencing/analysis status of samples in database

Usage: ./update_status.py <table> <config>

Arguments:
    <table>  table with bid, field, value rows (current acceptable fields: sequence_date, align_date, analysis_date, status
    <config>    json config file with genome, caller, and get/post urls

Options:
    -h
"""

import json
import sys

import requests
from docopt import docopt


def set_web_stuff(client, url):
    # set verify to False if testing
    client.get(url)
    return client.cookies['csrftoken'], dict(client.cookies), {"X-CSRFToken": client.cookies['csrftoken'],
                                                               "Referer": url}


def update_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, post_url, username, password) = (config_data['login_url'], config_data['urlUp'],
                                                 config_data['username'], config_data['password'])

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)
    if r.status_code == 200:
        sys.stderr.write('Successfully logged in\n')
    else:
        sys.stderr.write('Login failed for url ' + login_url + '\n got error code ' + str(r.status_code) + '\n')
        exit(1)

    table = open(args['<table>'], 'r')
    for line in table:
        (bid, field, value) = line.rstrip('\n').split('\t')
        updata = {'bnid': bid, field: value}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
        check = post_client.post(post_url, data=json.dumps(updata), headers=post_headers, cookies=post_cookies,
                                 allow_redirects=False)
        if check.status_code != 200:
            sys.stderr.write('Could not update information for ' + bid + ' ' + field + ' check connection and whether'
                            ' metadata exists for this sample\n')
        else:
            sys.stderr.write('Status for update ' + bid + ' ' + str(check.status_code) + '\n')

def main():
    update_status()


if __name__ == '__main__':
    main()
