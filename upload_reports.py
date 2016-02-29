#!/usr/bin/env python
"""
Plugin to interface with variant viewer - upload reports after pipeline is run.  Currently assume pairs...

Usage: ./upload_reports.py <list> <config>

Arguments:
    <list>  list of variant reports to upload
    <config>    json config file with genome, caller, and get/post urls

Options:
    -h
"""

import json
import os
import re
import sys
import pdb
import requests
from docopt import docopt


def get_info(bid, url, caller, genome):
    info_req = {'bid': bid, 'caller': caller, 'genome': genome}
    # cookies = dict(get_client.cookies)
    headers = {'Content-type': 'application/json'}  # ,  "X-CSRFToken": get_csrftoken}
    return requests.post(url, data=json.dumps(info_req), headers=headers)
    # return get_client.post(url, data=json.dumps(info_req), headers=headers, cookies=cookies)


def create_report_name(sample1, sample2, bid1, bid2):
    """

    :type sample2: object
    """
    sample1_name = sample1.json()['sample']
    sample2_name = sample2.json()['sample']
    sample1_desc = sample1.json()['description']
    sample2_desc = sample2.json()['description']
    # try to look for tumor/normal in sample name or desc
    root1 = re.search('(?i)(\S*\s*\S+)\s*(Tumor|T|Normal|N$)', sample1_name)
    try:
        # just want first letter to indicate T(umor) etc
        rname = root1.group(1) + ' ' + root1.group(2)[0].upper() + '/'
        root2 = re.search('(?i)(\S*\s*\S+)\s*(Tumor|T|Normal|N$)', sample2_name)
        rname += root2.group(2)[0].upper()
    except:
        sys.stderr.write('Finding T/N in sample failed, trying description\n')
        # just look for whole word in description, otherwise it's too much
        root1 = re.search('(?i)(tumor|normal)', sample1_desc)
        try:
            rname = sample1_name + root1.group(1)[0].upper() + '/'
            root2 = re.search('(?i)(tumor|normal)', sample2_desc)
            rname += root2.group(2)[0].upper()
        except:
            rname = sample1_name + '/' + sample2_name
    # reduce redundancy is 2nd part of name by seeing if year the same in bid
    rname += ' (' + bid1 + '/'
    b1 = re.search('(\d+)-(\d+)', bid1)
    b2 = re.search('(\d+)-(\d+)', bid2)
    if b1.group(1) == b2.group(1):
        rname += b2.group(2) + ')'
    else:
        rname += bid2 + ')'
    return rname


def set_web_stuff(client, url):
    client.get(url)
    return client.cookies['csrftoken'], dict(client.cookies), {"X-CSRFToken": client.cookies['csrftoken'],
                                                               "Referer": url}


# get config variables
def upload_reports():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (login_url, get_url, post_url, genome, caller, username, password) = (
        config_data['login_url'], config_data['urlGet'], config_data['urlUp'], config_data['genome'],
        config_data['caller'],
        config_data['username'], config_data['password'])

    # get token to gain access to site
    # get_client = requests.session()
    # get_client.get(login_url)
    # get_csrftoken = get_client.cookies['csrftoken']

    post_client = requests.session()
    (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
    login_data = dict(username=username, password=password)
    r = post_client.post(login_url, login_data, cookies=post_cookies, headers=post_headers)

    for fn in open(args['<list>'], 'r'):
        fn = fn.rstrip('\n')
        bnids = re.match('^(\d+-\d+)_(\d+-\d+)', os.path.basename(fn))
        (bid1, bid2) = (bnids.group(1), bnids.group(2))

        sample1_obj = get_info(bid=bid1, url=get_url, caller=caller, genome=genome)
        pdb.set_trace()
        sample2_obj = get_info(bid=bid2, url=get_url, caller=caller, genome=genome)
        (bid1_pk, bid2_pk) = (sample1_obj.json()['bid_pk'], sample2_obj.json()['bid_pk'])
        study_pk = sample1_obj.json()['study']
        genome_pk = sample1_obj.json()['genome_pk']
        caller_pk = sample1_obj.json()['caller_pk']
        report_name = create_report_name(sample1=sample1_obj, sample2=sample2_obj, bid1=bid1, bid2=bid2)
        metadata = {'name': [report_name], 'study': [study_pk], 'bnids': (bid1_pk, bid2_pk), 'genome': [genome_pk],
                    'caller': [caller_pk]}
        files = {'report_file': (fn, open(fn, 'rb'), 'application/octet-stream')}
        (post_csrftoken, post_cookies, post_headers) = set_web_stuff(post_client, login_url)
        post_client.post(post_url, data=metadata, files=files, headers=post_headers, cookies=post_cookies,
                         allow_redirects=False)


def main():
    upload_reports()


if __name__ == '__main__':
    main()
