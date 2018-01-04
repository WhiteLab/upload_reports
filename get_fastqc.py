#!/usr/bin/env python
"""
To be run from variant viewer server - downloads and organizes fastqc stats file

Usage: ./get_fastqc.py <table> <config>

Arguments:
    <table>  table with bnids
    <config>    json config file with user, server, project_path, data_path

Options:
    -h
"""

import json
import sys
import os
import subprocess
from docopt import docopt


def get_fastq_qc():
    args = docopt(__doc__)
    config_data = json.loads(open(args.get('<config>'), 'r').read())
    (user, server, ppath, rpath) = (config_data['user'], config_data['server'], config_data['project_path'],
                                    config_data['data_path'])
    for bnid in open(args.get('<table>')):
        bnid = bnid.rstrip('\n')
        # remote path might differ from fixed local path
        fpath = rpath + '/' + bnid + '/QC/'
        lpath = 'FASTQC/' + bnid + '/QC/'
        list_stats = 'rsync --list-only ' + user + '@' + server + ':' + ppath + '/' + fpath
        sys.stderr.write('Searching for valid files ' + list_stats + '\n')
        contents = subprocess.check_output(list_stats, shell=True).decode()
        flist = contents.split('\n')
        for fn in flist:
            try:
                if fn[-11:] == 'fastqc.html':
                    new_fn = fn.split()
                    sys.stderr.write('QC file ' + new_fn[-1] + ' found!\n')
                    # check and make host dir since rsync can't do it because why make my life easier
                    if not os.path.isdir(lpath):
                        create_path = 'mkdir -p ' + lpath
                        sys.stderr.write('Creating directory path ' + create_path + '\n')
                        subprocess.call(create_path, shell=True)
                    dl_file = 'rsync -rt ' + user + '@' + server + ':' + ppath + '/' + fpath + new_fn[-1] + ' ' \
                              + lpath + new_fn[-1]
                    sys.stderr.write('Downloading desired QC file ' + dl_file + '\n')
                    subprocess.call(dl_file, shell=True)
            except:
                sys.stderr.write('Lazy file name matching failed on ' + fn + 'ignore!\n')


def main():
    get_fastq_qc()


if __name__ == '__main__':
    main()
