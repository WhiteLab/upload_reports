import sys


def set_web_stuff(client, url, vflag):
    # set verify to False if testing
    if vflag == 'Y':
        client.get(url)
    else:
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        client.get(url, verify=False)
    return client.cookies['csrftoken'], dict(client.cookies), {"X-CSRFToken": client.cookies['csrftoken'],
                                                               "Referer": url}


def db_connect(database, username, password, host):
    import psycopg2
    try:
        constring = "dbname=" + database + " user=" + username + " password=" + password + " host=" + host
        return psycopg2.connect(constring)
    except:
        sys.stderr.write('Failed connection\n')
        exit(1)