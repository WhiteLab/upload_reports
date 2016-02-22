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

def create_report_name(sample1, sample2, bid1, bid2):
    """

    :type sample2: object
    """
    sample1_name = sample1.json()['sample']
    sample2_name = sample2.json()['sample']
    sample1_desc = sample1.json()['description']
    sample2_desc = sample2.json()['description']
    # try to look for tumor/normal in sample name or desc
    root1 = re.search('(?i)(\S+)\s*(Tumor|T|Normal|N$)', sample1_name)
    try:
        # just want first letter to indicate T(umor) etc
        rname = root1.group(1) + ' ' + root1.group(2)[0].upper() + '/'
        root2 = re.search('(?i)(\S+)\s*(Tumor|T|Normal|N$)', sample2_name)
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


for fn in open(args['<list>'], 'r'):
    fn = fn.rstrip('\n')

    bnids = re.match('^(\d+-\d+)_(\d+-\d+)', fn)
    (bid1, bid2) = (bnids.group(1), bnids.group(2))
    sample1_obj = get_info(bid1, get_url)
    sample2_obj = get_info(bid2, get_url)
    study = sample1_obj.json()['study']
    report_name = create_report_name(sample1=sample1_obj, sample2=sample2_obj, bid1=bid1, bid2=bid2)


    # TO DO - parse for tumor normal, generate report name
    # upload using requests.put and requests.file into upload_report method of viewer


