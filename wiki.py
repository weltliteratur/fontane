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
# 2020-08-24 (rja)
# - smaller cleanups
# 2019-07-02 (ms)
# - added column page views in stats
# - fixed bug (sep instead of separator)
# 2019-05-19 (rja)
# - fixed problem with missing English version
# - added option --file
# 2019-05-14 (rja)
# - initial version

import pywikibot
import collections
import sys
import argparse
import pageviewapi

version = "0.0.4"


# returns the following page stats:
# - number of characters of the (Wiki markup) text
# - number of contributors
# - number of revisions
# - number of outgoing external links
# - number of outgoing interwiki links
# - number of language editions
# - number of linked pages
# - number of ingoing links (backlinks)
# - number of categories
# - datetime of first revision
# TODO:
# - number of top-level sections
# - number of outgoing links
def get_page_stats(start_date, end_date, page):
    d = collections.OrderedDict()  # keep insertion order

    # Wikipedia
    # see https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html#module-pywikibot.page
    d["textlen"]    = len(page.text)                                     # FIXME: use plain text
    d["contribs"]   = len(set([c for c in page.contributors()]))         # TODO: ignore IP addresses and bots?
    d["revisions"]  = len([r for r in page.revisions()])
    d["extlinks"]   = len([e for e in page.extlinks()])                  # TODO: figure out meaning
    d["interlinks"] = len(get_interwiki(page))                           # of all those different
    d["interlang"]  = len([i for i in page.langlinks()])                 # types of links
    d["linkedpag"]  = len([i for i in page.linkedPages(namespaces=[0])]) #
    d["backlinks"]  = len([b for b in page.backlinks(namespaces=[0])])   # 0 = article namespace
    d["categories"] = len([c for c in page.categories()])                # TODO: some not meaningful
    d["firstrev"]   = get_first_revision(page).timestamp
    # d["title"] = page.title()
    # d["country_code"] = page.site.code

    # Wikidata
    # see https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html#pywikibot.ItemPage
    d["claims"]    = len(page.data_item().get()["claims"])               # available keys: claims, labels, aliases, descriptions, sitelinks
    d["pageviews"] = get_pageviews(start_date, end_date, page)           # see https://pypi.org/project/pageviewapi/

    return d


# uses pageview api to count page views in time range for each page respectively
def get_pageviews(start_date, end_date, page):
    views = 0
    try:
        out = pageviewapi.per_article(page.site.code + '.wikipedia', page.title(), start_date, end_date,
                                      access='all-access', agent='all-agents', granularity='daily')
        for i in range(len(out["items"])):
            views += out["items"][i]["views"]
        return views
    except pageviewapi.client.ZeroOrDataNotLoadedException:
        return 0


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
    # what to do
    parser.add_argument('-l', '--languages', type=str, metavar="ART", help='stats for articles versions in all available languages')
    parser.add_argument('-c', '--category', type=str, metavar="CAT", help='stats for articles of a category')
    parser.add_argument('-f', '--file', type=argparse.FileType('r', encoding='utf-8'), metavar="FILE", help='file to use as input')
    parser.add_argument('-t', '--test', type=str, metavar="ART", help='test article')
    # options
    parser.add_argument('-s', '--sep', type=str, metavar="SEP", help='output column separator', default='\t')
    parser.add_argument('-L', '--lang', type=str, metavar="LANG", help='language edition to be used', default='de')
    parser.add_argument('-S', '--site', type=str, metavar="SITE", help='site to be used', default='wikipedia')
    parser.add_argument('-v', '--version', action="version", version="%(prog)s " + version)
    parser.add_argument('-p', '--start', type=str, metavar="START", help='format: YYYYMMDD - start date for counting page views', default='20190101')
    parser.add_argument('-q', '--end', type=str, metavar="END", help='format: YYYYMMDD - end date for counting page views', default='20191231')
    args = parser.parse_args()

    # We are using the German language edition of Wikipedia for all
    # queries.
    site = pywikibot.Site(args.lang, args.site)

    # decide what to do
    if args.category:
        # Given the (German) name of a category, extract statistics
        # for all articles belonging to that category.
        page = pywikibot.Category(site, args.category)

        # check, whether this really is a category page
        if not page.is_categorypage():
            sys.exit(args.category + " is not a category page")

        for i, a in enumerate(page.articles(namespaces=[0])):
            stats = get_page_stats(args.start, args.end, a)
            print_stats(i, a.title(), stats, args.sep)

    if args.languages:
        # Given the (German) name of an article, extract statistics
        # for all available language editions.
        #
        page = pywikibot.Page(site, args.languages)

        # FIXME: queried language itself is missing, so we add it here :-(
        sitestats = {site.code: get_page_stats(args.start, args.end, page)}

        # get stats for other language editions
        for langlink in page.langlinks():
            # we are using site.code, since site.lang can be the same
            # for different wikis (e.g., wikipedia:en and
            # wikipedia:simple both have "en" as site.lang)
            sitestats[langlink.site.code] = get_page_stats(args.start, args.end, pywikibot.Page(langlink.site, langlink.title))

        # print stats
        for i, lang in enumerate(sorted(sitestats)):
            print_stats(i, lang, sitestats[lang], args.sep)

    if args.file:
        # given a file with (currently) four columns:
        # http://www.wikidata.org/entity/Q34787   Friedrich Engels        168	https://de.wikipedia.org/wiki/Friedrich_Engels
        # print statistics for the entity in column two from the German Wikipedia

        i = 0
        for line in args.file:
            s, desc, linkcount, url = line.strip().split('\t')
            # skip first line, if it is the header
            if not (s == "s" and desc == "desc"):
                # get stats for URL
                #
                # FIXME: we manually extract the name of the page from
                # its URL, it would be better to do use the correct
                # API method
                name = url[len("https://de.wikipedia.org/wiki/"):]
                page = pywikibot.Page(site, name)
                print_stats(i, desc, get_page_stats(args.start, args.end, page), args.sep)
                i = i + 1

    if args.test:
        # TODO: some code to test the API ... remove upon cleanup

        # test .title() for category
        page = pywikibot.Category(site, args.test)

        # check, whether this really is a category page
        if not page.is_categorypage():
            sys.exit(args.category + " is not a category page")

        for i, a in enumerate(page.articles(namespaces=[0])):
            print(i, a.title())

        # test dbName()
        if False:
            print("--- starting with de")
            for langlink in page.langlinks():
                print(langlink.site, langlink.site.lang, langlink.site.dbName(), langlink.site.code)

        # test Wikidata
        if False:
            data = page.data_item()
            claims = data.get()["claims"]  # claims, labels, aliases, descriptions, sitelinks
            for d in claims:
                print(d, claims[d])
