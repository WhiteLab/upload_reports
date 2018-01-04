#!/usr/bin/env python
"""
To be run from variant viewer server - downloads and organizes alignment stats file

Usage: ./get_align_qc.py <table> <config>

Arguments:
    <table>  table with bnids
    <config>    json config file with user, server, project_path, data_path

Options:
    -h
"""

import json
import sys
import subprocess
from docopt import docopt


def update_status():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (user, server, ppath, dpath) = (config_data['user'], config_data['server'], config_data['project_path'],
                                    config_data['data_path'])
    for bnid in open(args.get('<table>')):
        bnid = bnid.rstrip('\n')
        fpath = dpath + '/' + bnid + '/QC'
        list_stats = 'rsync --list-only ' + user + '@' + server + ':' + ppath + '/' + fpath
        contents = subprocess.check_output(list_stats, shell=True).decode()
        flist = contents.split('\n')
        for fn in flist:
            try:
                if fn[-13:] == 'qc_stats.json':
                    new_fn = fn.split()
                    sys.stderr.write('QC file ' + new_fn[-1] + ' found!\n')
                    dl_file = 'rsync --rt ' + user + '@' + server + ':' + ppath + '/' + fpath + '/' + new_fn[-1] + ' ' \
                              + fpath + '/' + new_fn[-1]
                    sys.stderr.write('Downloading desired QC file ' + dl_file + '\n')
                    subprocess.call(dl_file, shell=True)
            except:
                sys.stderr.write('Lazy file name matching failed on ' + fn + 'ignore!\n')


def main():
    update_status()


if __name__ == '__main__':
    main()
