#!/usr/bin/python3
# -*- coding: utf-8 -*-

#
# Extract statistics from Wikipedia/Wikidata
#
# Usage: python3 core_stable/pwb.py wiki.py --help
# 
# Author: rja 
#
# Changes:
# 2019-05-14 (rja)
# - initial version 

import re
import pywikibot
import collections
import sys
import argparse

version = "0.0.1"

# returns the following page stats:
# - length = number of characters
# - number of top-level sections
# - number of language editions
# - number of outgoing links
# - number of outgoing external links
# - number of outgoing interwiki links
# - number of ingoing (backlinks)
# - number of categories
# - number of revisions
# - number of contributors
#
def get_page_stats(page):
    d = collections.OrderedDict() # keep insertion order
    
    # Wikipedia
    # see https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html#module-pywikibot.page
    d["textlen"]    = len(page.text)                                       # FIXME: use plain text
    d["contribs"]   = len(set([c for c in page.contributors()]))           # TODO: ignore IP addresses and bots?
    d["revisions"]  = len([r for r in page.revisions()])
    d["extlinks"]   = len([e for e in page.extlinks()])                    # TODO: figure out meaning
    d["interlinks"] = len(get_interwiki(page))                             #       of all those different
    d["interlang"]  = len([i for i in page.langlinks()])                   #       types of links
    d["linkedpag"]  = len([i for i in page.linkedPages(namespaces = [0])]) # 
    d["backlinks"]  = len([b for b in page.backlinks(namespaces = [0])])   # 0 = article namespace
    d["categories"] = len([c for c in page.categories()])                  # TODO: some not meaningful

    # Wikidata
    # see https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html#pywikibot.ItemPage
    # item = page.data_item()

    return d

# to avoid exception on https://az.wikipedia.org/wiki/Teodor_Fönten
def get_interwiki(page):
    try:
        return [i for i in page.interwiki()]
    except ValueError:
        return []

# stats about one page and its different language versions
def page_in_different_languages(name, sep):
    site = pywikibot.Site("en", "wikipedia")
    page = pywikibot.Page(site, name)
    
    # get all language versions
    for i, l in enumerate(page.langlinks()):
        print("next is", l.site, file=sys.stderr)
        # get stats for site
        stats = get_page_stats(pywikibot.Page(l.site, l.title))
        print_stats(i, l.site, stats, sep)
            
# print statistics
def print_stats(i, name, stats, sep):
    # header
    if i == 0:
        print("# name", sep.join(stats.keys()), sep=sep)
        # data
    print(name, sep.join([str(c) for c in stats.values()]), sep=sep)
    
def iter_stats(names, sep):
    names = ["Theodor Fontane"]
    site = pywikibot.Site("en", "wikipedia")
    for i, name in enumerate(names):
        page = pywikibot.Page(site, name)
        stats = get_page_stats(page)
        print_stats(i, name, stats, sep)
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract stats from Wikipedia', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--languages', type=str, metavar="ARTICLE", help='stats for languages')
    parser.add_argument('-s', '--separator', type=str, metavar="SEP", help='output column separator', default='\t')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)

    args = parser.parse_args()

    # iter_stats(names, args.sep)
    if args.languages:
        page_in_different_languages(args.languages, args.separator)
