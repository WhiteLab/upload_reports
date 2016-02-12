#!/usr/bin/env python
"""
Plugin to interface with variant viewer - upload reports after pipeline is run.  Currently assume pairs...

Usage: ./upload_reports.py <list> <urlGet> <urlUp>

Arguments:
    <list>  list of variant reports to upload
    <urlGet>   url to query
    <urlUp>    url to upload to

Options:
    -h
"""
import requests
import json
import sys
import re
import pdb
from docopt import docopt

args = docopt(__doc__)
get_url = args['<urlGet>']
def get_info(bid, url):
    url = url + bid + '/'
    return requests.get(url)

for fn in open(args['<list>'], 'r'):
    fn = fn.rstrip('\n')

    bnids = re.match('^(\d+-\d+)_(\d+-\d+)', fn)
    (bid1, bid2) = (bnids.group(1), bnids.group(2))
    sample1_obj = get_info(bid1, get_url)
    sample2_obj = get_info(bid2, get_url)
    study = sample1_obj.json()['study']
    sample1 = sample1_obj.json()['sample']
    sample2 = sample2_obj.json()['sample']
    pdb.set_trace()
    # TO DO - parse for tumor normal, generate report name
    # upload using requests.put and requests.file into upload_report method of viewer


