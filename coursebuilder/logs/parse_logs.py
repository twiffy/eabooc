import re
import sys
import urlparse
import numpy as np
# 61.15.233.32 - - [29/Sep/2013:00:00:55 -0700] "GET / HTTP/1.1" 302 206 - "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.76 Safari/537.36" "booc-iu.appspot.com" ms=89 cpu_ms=64 cpm_usd=0.000023 instance=00c61b117ce11bb3846d96f1e2d4b4415a896d2e app_engine_release=1.8.5

line_regex = re.compile(
        r'^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<date>.*?)\] "(?P<method>\S+)\s+(?P<path>.*?)\s+HTTP/1\.\d" (?P<status>\d+) (?P<size>\d+) (?:"(?P<referer>.*?)"|-) (?:"(?P<agent>.*?)"|-) "(?P<vhost>.*?)" (?P<extra>.*?)$'
    )

from collections import defaultdict


def parse_lines(lines):
    for line in lines:
        match = line_regex.match(line)
        if match:
            fields = {k:v for k,v in (
                part.split('=') for part in (
                    match.group('extra').split()))}
            fields.update(match.groupdict())
            yield fields
        else:
            print >> sys.stderr, "NOT HAPPY:", line

def response_times_by_stuff(lines):
    response_times = defaultdict(list)
    for fields in parse_lines(lines):
        if 'instance' not in fields:
            continue
        
        if '?' in fields['path']:
            path, query_str = fields['path'].split('?', 1)
            query = urlparse.parse_qs(query_str)
            if 'action' in query:
                ident = ' '.join((path, query['action'][0]))
            else:
                ident = path
        else:
            ident = fields['path']
        response_times[ident].append(int(fields['ms']))

    for path, times in response_times.iteritems():
        print path, 'median of', len(times), 'times is', np.median(times)

#response_times_by_stuff(sys.stdin)

from collections import Counter
from urlparse import urlparse

def shares(lines):
    referers = Counter()
    shares = defaultdict(set)
    spookies = set()
    for fields in parse_lines(lines):
        ref = fields['referer']
        if ref:
            ref = urlparse(ref).hostname
        referers[ref] += 1


        if 'unit=' not in fields['path']:
            if 'Twitterbot' in fields['agent']:
                shares['twitter'].add(fields['path'])
            elif 'facebookexternalhit' in fields['agent']:
                shares['facebook'].add(fields['path'])
            elif 'Googlebot' in fields['agent']:
                shares['googlebot'].add(fields['path'])
            elif 'msnbot' in fields['agent']:
                shares['msnbot'].add(fields['path'])
            elif 'bitlybot' in fields['agent']:
                shares['bitly'].add(fields['path'])
            elif 'bot' not in fields['agent'] and not fields['referer']:
                shares['maybe-email'].add(fields['path'])
                spookies.add(fields['ip'])



    for ref, count in referers.iteritems():
        print count, ref
    print '--------------'

    for site, urls in shares.iteritems():
        print site, len(urls)
    print '--------------'

    print len(spookies), 'unique IPs accessed evidence with no referrer - maybe e-mail?'



shares(sys.stdin)
