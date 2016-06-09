#!/usr/bin/env python
"""
Plugin/cronjob to sync project-specific sequencing info between bionimbus web and variant viewer, also initialize
statuses for stuff already in vv, but without a status

Usage: ./sync_seq_info.py <config>

Arguments:
    <config>    json config file with genome, caller, and get/post urls

Options:
    -h
"""

import json
import sys
import requests
import pdb
from docopt import docopt
from login_tools import set_web_stuff
from login_tools import db_connect


def check_seq_status(db, bnid):
    query = "SELECT F.created_on FROM t_file F WHERE F.f_bionimbus_id=%s AND F.is_active='T'"
    sys.stderr.write(query + ' ' + bnid + '\n')
    cur = db.cursor()
    cur.execute(query, (bnid,))
    entry = cur.fetchone()
    return entry


def update_status(bnid, seq_date, post_client, login_url, set_status_url, field, status, vflag):
        to_update = {'bnid': bnid, field: seq_date}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url, vflag)
        check = post_client.post(set_status_url, data=json.dumps(to_update), headers=post_headers, cookies=post_cookies,
                                 allow_redirects=False)
        if check.status_code != 200:
            sys.stderr.write('Could not set submit date for ' + bnid + '\n')
            return 1
        to_update = {'bnid': bnid, 'status': status}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url, vflag)
        check = post_client.post(set_status_url, data=json.dumps(to_update), headers=post_headers, cookies=post_cookies,
                                 allow_redirects=False)
        if check.status_code != 200:
            sys.stderr.write('Could not set seq status')
            return 1
        sys.stderr.write('Updated status ' + status + ' for ' + bnid + '\n')
        return 0


def sync_seq_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, username, password, get_status_url, db_user, db_pw, db_host, database, set_status_url, vflag) = \
        (config_data['login_url'], config_data['username'], config_data['password'], config_data['urlGetStatus'],
         config_data['dbUser'], config_data['dbPw'], config_data['dbHost'], config_data['db'],
         config_data['setStatusUrl'], config_data['vflag'])

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url, vflag)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)
    # get list of bnids to check bionimbus web for
    if r.status_code == 200:
        sys.stderr.write('Successfully logged in\n')
    else:
        sys.stderr.write('Login failed for url ' + login_url + '\n got error code ' + str(r.status_code) + '\n')
    status_info = post_client.get(get_status_url, params=login_data)
    # check bionimbus web for samples that have been sequenced
    con = db_connect(database, db_user, db_pw, db_host)
    for bnid in status_info.json():
        status = status_info.json()[bnid]
        if status == 'Sample submitted for sequencing':
            seq_date = check_seq_status(con, bnid)
            if seq_date is not None:
                update_status(bnid, str(seq_date[0]), post_client, login_url, set_status_url,
                              'sequence_date', 'SEQUENCED', vflag)


def main():
    sync_seq_status()


if __name__ == '__main__':
    main()