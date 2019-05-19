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

version = "0.0.2"

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
# - datetime of first revision
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
    d["firstrev"]   = get_first_revision(page).timestamp

    # Wikidata
    # see https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html#pywikibot.ItemPage
    d["claims"] = len(page.data_item().get()["claims"]) # available keys: claims, labels, aliases, descriptions, sitelinks

    return d

# to avoid exception on https://az.wikipedia.org/wiki/Teodor_Fönten (due to a syntax error?)
def get_interwiki(page):
    try:
        return [i for i in page.interwiki()]
    except ValueError:
        return []

def get_first_revision(page):
    last = None
    for last in page.revisions():
        pass
    return last

# print statistics
def print_stats(i, name, stats, sep):
    # header
    if i == 0:
        print("# name", sep.join(stats.keys()), sep=sep)
        # data
    print(name, sep.join([str(c) for c in stats.values()]), sep=sep)


# main method - program control flow starts here
if __name__ == '__main__':

    # parse command line arguments
    parser = argparse.ArgumentParser(description='Extract stats from Wikipedia', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--languages', type=str, metavar="ARTICLE", help='stats for articles versions in all available languages')
    parser.add_argument('-c', '--category', type=str, metavar="CATEGORY", help='stats for articles of a category')
    parser.add_argument('-s', '--separator', type=str, metavar="SEP", help='output column separator', default='\t')
    parser.add_argument('-t', '--test', type=str, metavar="ARTICLE", help='test article')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)
    args = parser.parse_args()

    # decide what to do
    if args.category:
        # given the (German) name of a category, extract statistics
        # for all articles belonging to that category
        site = pywikibot.Site("de", "wikipedia")
        page = pywikibot.Category(site, args.category)

        # check, whether this really is a category page
        if not page.is_categorypage():
            sys.exit(args.category + " is not a category page")

        for i, a in enumerate(page.articles(namespaces = [0])):
            stats = get_page_stats(a)
            # FIXME: a.title does not work well
            print_stats(i, a.title, stats, args.separator)

    if args.languages:
        # Given the (English) name of an article, extract statistics
        # for all available language versions.
        #
        # FIXME: We start with the English Wikipedia, since in the
        # German Wikipedia, "en" and "simple" are both abbreviated
        # "en".
        site = pywikibot.Site("en", "wikipedia")
        page = pywikibot.Page(site, args.languages)

        # FIXME: For some reason, queried site itself is missing :-(
        sitestats = {site.lang : get_page_stats(page)}

        # get stats for other sites
        for langlink in page.langlinks():
            sitestats[langlink.site.lang] = get_page_stats(pywikibot.Page(langlink.site, langlink.title))

        # print stats
        for i, lang in enumerate(sorted(sitestats)):
            print_stats(i, lang, sitestats[lang], args.separator)

    if args.test:
        # test Wikidata
        site = pywikibot.Site("de", "wikipedia")
        page = pywikibot.Page(site, args.test)

        # datetime of first revision
        for r in page.revisions():
            print(r.revid, r.timestamp)


        # Wikidata
        if False:
            data = page.data_item()
            claims = data.get()["claims"] # claims, labels, aliases, descriptions, sitelinks
            for d in claims:
                print(d, claims[d])
