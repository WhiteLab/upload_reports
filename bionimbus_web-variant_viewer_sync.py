#!/usr/bin/env python
"""
Plugin/cronjob to sync project-specific info between bionimbus web and variant viewer

Usage: ./bionimbus_web-variant_viewer_sync.py <config>

Arguments:
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

def sync_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, post_url, username, password) = (config_data['login_url'], config_data['urlUp'],
                                                 config_data['username'], config_data['password'])

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)
    # get list of studies to check bionimbus web for

    # query bionimbus web for all with project and subproject (study)

    # populate variant viewer with metadata for relevant studies if not populated already

    # check variant viewer for status submitted for sequencing

    # check bionimbus web to see if tfile exists, indicating it's been sequenced



def main():
    sync_status()


if __name__ == '__main__':
    main()
