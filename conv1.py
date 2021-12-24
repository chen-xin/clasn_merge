
import yaml
from pathlib import Path
from datetime import datetime
import time
import re
import random
import urllib.request

from special_conf import provider_confs
###############################################################################
# Utils
###############################################################################

def fetch_profile(url):
    req = urllib.request.Request(url=url, method='GET')

    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    # req.add_header("Accept-Encoding", "gzip, deflate, br")
    # req.add_header("Accept-Language", "en-US,en;q=0.5")
    req.add_header("Connection", "keep-alive")
    # req.add_header("Host", "sub.9ups.xyz")
    req.add_header("Upgrade-Insecure-Requests", "1")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0")

    with urllib.request.urlopen(req) as f:
        result = f.read().decode('utf-8', errors='ignore')

    return result

def get_wsl_userprofile():
    import subprocess

    result = subprocess.run(['cmd.exe', '/c',  'echo',  '%UserProfile%'], stdout = subprocess.PIPE)
    result = subprocess.run(['wslpath', result.stdout.decode('utf-8')], stdout = subprocess.PIPE)
    return result.stdout.decode('utf-8').strip()

def read_yaml(filename):
    # with FileInput(files=(filename)) as input:
    with open(filename) as input:
        data = yaml.safe_load(input.read())
    return data

def save_yaml(data, filename):
    with open(filename, 'w', encoding='utf8') as output:
        yaml.dump(data, output, allow_unicode=True, sort_keys=False)

###############################################################################
# Rules
###############################################################################

def get_providers(list_file='', always_download=False):
    if list_file=='':
        user_profile = get_wsl_userprofile()
        list_file = Path(user_profile, '.config/clash/profiles/list.yml')
        providers = read_yaml(list_file)['files']
        providers = [p for p in providers if p['url'][:4]=='http']
    else:
        providers = read_yaml(list_file)

    providers = [
        { 'name': p['name'],
         'url': p['url'],
         'filename': Path(Path(list_file).parent, p['time']) if not always_download and 'time' in p else '' }
        for p in providers ]

    return providers

def get_profile(name, url, filename=''):
    if filename == '':
        profile = yaml.safe_load(fetch_profile(url))
    else:
        print('Using local profile: %s'%filename)
        with open(filename) as f:
            profile = yaml.safe_load(f.read())

    proxies = profile['proxies']
    rules = profile['rules']

    for p in proxies:
        p['name'] = p['name'].replace('#', '※').replace('|', '_')

    return { 'proxies': proxies, 'rules': rules }

def get_profiles(providers):
    print(providers)
    profiles = []
    for p in providers:
        try:
            profiles.append({ **p, **get_profile(**p) })
        except Exception as e:
            print(e)
            continue
    return profiles


def insert_extra_proxies(insertion:str, additional_proxies:list):
    def _insert_proxies(proxies:list):
        if insertion in proxies:
            ind = proxies.index(insertion)
            proxies = proxies[:ind] + additional_proxies + proxies[ind+1:]
        return proxies
    return _insert_proxies

def get_names(proxies):
    return [p['name'] for p in proxies]


def generate_proxy_groups(profiles):

    add_to_auto = []
    add_to_warmane = []
    # sort proxies, make low cost proxy first
    for pg in profiles:
        ns = get_names(pg['proxies'])
        if pg['name'] in provider_confs:
            ns.sort(key=provider_confs[pg['name']]['order_fn'])
            # provider_confs[pg['name']]['order_fn'](ns)
            add_to_warmane += provider_confs[pg['name']]['warmane_filter'](ns)
        add_to_auto += ns[:10]

    proxy_groups = read_yaml('_proxy-groups.yaml')['proxy-groups']

    all_proxies = [ proxy for p in profiles for proxy in p['proxies']]

    all_proxie_names = set(
        get_names(all_proxies) +
        get_names(proxy_groups) +
        get_names(profiles) +
        ['🐷 节点选择(所有)', 'DIRECT', 'REJECT', '🎯 全球直连']
    )

    insertion_confs = { k: insert_extra_proxies(k, v)
                       for k, v in {
                           'INSERT ALL_PROVIDERS': [p['name'] for p in profiles],
                           'INSERT PRIOR_PROXIES': add_to_auto,
                           'INSERT 🎮 warmane': add_to_warmane }.items()
    }

    for pg in proxy_groups:
        for k, v in insertion_confs.items():
            pg['proxies'] = v(pg['proxies'])
        pg['proxies'] = [ p for p in pg['proxies'] if p in all_proxie_names]

    proxy_groups = [ #select_proxy,
                    *proxy_groups,
                    *[ {'name': profile['name'],
                      'type': 'select',
                      'proxies': [p['name'] for p in profile['proxies']]}
                     for profile in profiles] ]
    return { 'proxies': all_proxies, 'proxy-groups': proxy_groups }

def create_rules(profiles, name):
    for p in profiles:
        if p['name'] == name:
            additional_rules = read_yaml('_additional_rules.yaml')['rules']
            # rules = additional_rules + [ r.replace('🔰 节点选择', '🔰 自动选择') for r in p['rules']]
            rules = additional_rules + p['rules']
            return rules

    print('Profile [%s] not found, using last config'%name)

    rules = read_yaml('output/output.yaml')['rules']
    return rules

def merge_confs(conf_file, output, keys):
    conf = read_yaml(conf_file)
    save_yaml({ **conf, **keys }, output)

def proxy_order_limi(proxies):
    pattern = '\d.\d+X'


###############################################################################
# main
###############################################################################

if __name__ == '__main__':
    profiles = get_profiles(get_providers())
    proxies = generate_proxy_groups(profiles)
    rules = create_rules(profiles, 'edu.lovess.top_20251210')

    keys = {**proxies, 'rules': rules }
    merge_confs('_config.cfw.yaml', 'output/output.yaml', keys)
    merge_confs('_config.yaml', 'output/config.yaml', keys)

