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
import psycopg2
import re
from docopt import docopt


def set_web_stuff(client, url):
    # set verify to False if testing
    client.get(url)
    return client.cookies['csrftoken'], dict(client.cookies), {"X-CSRFToken": client.cookies['csrftoken'],
                                                               "Referer": url}


def db_connect(database, username, password, host):
    try:
        constring = "dbname=" + database + " user=" + username + " password=" + password + " host=" + host
        return psycopg2.connect(constring)
    except:
        sys.stderr.write('Failed connection\n')
        exit(1)


def check_variant_viewer(result, sid, login, get_bnid, client, to_add, date_dict):
    # get all study-related info at once to check
    getUrl = get_bnid + str(sid) + '/'
    study_info = client.get(getUrl, params=login)
    bnid_dict = {}
    for key in study_info.json():
        bnid = re.search('(\d+-\d+)\)$', study_info.json()[key])
        bnid_dict[bnid.group(1)] = 1
    for entry in result:
        (study, sample, bnid, d1, d2, cell, date) = entry
        if bnid not in bnid_dict:
            if d1 is not None:
                desc = d1
                if d2 is not None:
                    desc = desc + ' ' + d2
            elif d2 is not None:
                desc = d2
            else:
                desc = 'NA'
            if cell is None:
                cell = 'NA'
            to_add['sheet'].append((study, sample, bnid, desc, cell))
            date_dict[bnid] = date
            sys.stderr.write('Found new entry to add for bionimbus id ' + bnid + ' sample ' + sample + '\n')
    return to_add, date_dict


def query_bionimbus_web(conn, subproj):
    if subproj != 'PDX':
        # planning on using sample and treatment fields as part of experiment description
        query = "SELECT S.f_name, EU.f_name, EU.f_bionimbus_id, EU.f_sample, EU.f_treatment, EU.f_source, " \
                "EU.created_on FROM t_experiment_unit EU, t_subproject S WHERE EU.f_subproject=S.id AND S.f_name=%s " \
                "AND  EU.is_active='T'"
    else:
        query = "SELECT P.f_name, EU.f_name, EU.f_bionimbus_id, EU.f_sample, EU.f_treatment, EU.f_source, " \
                "EU.created_on FROM  t_experiment_unit EU, t_project P WHERE EU.f_project=P.id AND P.f_name=%s " \
                "AND  EU.is_Active='T'"
    sys.stderr.write(query + '\n')
    cur = conn.cursor()
    cur.execute(query, (subproj,))
    entries = cur.fetchall()
    return entries


def sync_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, post_url, username, password, get_study_url, get_bnid_url, db_user, db_pw, db_host, database,
     post_meta_url, set_status_url) = (config_data['login_url'], config_data['urlUp'], config_data['username'],
         config_data['password'], config_data['urlGetStudy'], config_data['urlGetBnid'], config_data['dbUser'],
         config_data['dbPw'], config_data['dbHost'], config_data['db'], config_data['postMetaUrl'],
                                         config_data['setStatusUrl'])

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)
    # get list of studies to check bionimbus web for
    if r.status_code == 200:
        sys.stderr.write('Successfully logged in\n')
    else:
        sys.stderr.write('Login failed for url ' + login_url + '\n got error code ' + str(r.status_code) + '\n')
        exit(1)

    # query bionimbus web for all with project and sub project (study)
    study_info = post_client.get(get_study_url, params=login_data)
    if study_info.status_code != 200:
        sys.stderr.write('Lookup request failed.  Check cookies and tokens and try again\n')
        exit(1)
    con = db_connect(database, db_user, db_pw, db_host)
    # dict of rows to add to mimic sheet submission
    to_add = {'sheet': []}
    # dict for setting date of submission
    date_dict = {}
    for key in study_info.json():
        # adding pk for study to leverage metadata lookup function get_bnid_by_study
        entries = query_bionimbus_web(con, key)
        if len(entries) > 0:
            (to_add, date_dict) = check_variant_viewer(entries, study_info.json()[key], login_data, get_bnid_url,
                                                       post_client, to_add, date_dict)

    # populate variant viewer with metadata for relevant studies if not populated already
    if len(to_add) > 0:

        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
        # post_headers.update({'name': 'sheet'})
        check = post_client.post(post_meta_url, data=json.dumps(to_add), headers=post_headers,
                                 cookies=post_cookies, allow_redirects=False)
        if check.status_code == 500:
            sys.stderr.write('Adding new metadata failed!\n')
            exit(1)
        sys.stderr.write('Created new entries in variant viewer\n')
    # set variant viewer for status submitted for sequencing for newly added stuff
    for new_entry in to_add['sheet']:
        bnid = new_entry[2]
        # date_dict has datetime objects, need to convert to to str
        to_update = {'bnid': bnid, 'submit_date': str(date_dict[bnid])}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
        check = post_client.post(set_status_url, data=json.dumps(to_update), headers=post_headers, cookies=post_cookies,
                                 allow_redirects=False)
        if check.status_code != 200:
            sys.stderr.write('Could not set submit date for ' + bnid + '\n')
        status = 'Sample submitted for sequencing'
        to_update = {'bnid': bnid, 'status': status}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
        check = post_client.post(set_status_url, data=json.dumps(to_update), headers=post_headers, cookies=post_cookies,
                                 allow_redirects=False)
        if check.status_code != 200:
            sys.stderr.write('Could not set seq status')
        sys.stderr.write('Updated submission status for samples\n')


def main():
    sync_status()


if __name__ == '__main__':
    main()
