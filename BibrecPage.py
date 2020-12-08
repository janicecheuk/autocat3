#!/usr/bin/env python
#  -*- mode: python; indent-tabs-mode: nil; -*- coding: utf-8 -*-

"""
BibrecPage.py

Copyright 2009-2010 by Marcello Perathoner

Distributable under the GNU General Public License Version 3 or newer.

The bibrec page.

"""

from __future__ import unicode_literals

import cherrypy

from libgutenberg import GutenbergGlobals as gg
from i18n_tool import ugettext as _
from i18n_tool import ungettext as __

import BaseSearcher
import Page


class BibrecPage(Page.Page):
    """ Implements the bibrec page. """

    def index(self, **dummy_kwargs):
        """ A bibrec page. """

        os = BaseSearcher.OpenSearch()

        os.log_request('bibrec')

        dc = BaseSearcher.DC()

        # the bulk of the work is done here
        dc.load_from_database(os.id)
        if not dc.files:
            # NOTE: Error message
            raise cherrypy.HTTPError(404, _('No ebook by that number.'))

        # add these fields so we won't have to test for their existence later
        dc.extra_info = None
        dc.url = None

        dc.translate()
        dc.header = gg.cut_at_newline(dc.title)
        os.title = dc.make_pretty_title()
        dc.extra_info = ''
        dc.class_ = BaseSearcher.ClassAttr()
        dc.order = 10
        dc.icon = 'book'
        if 'Sound' in dc.categories:
            dc.icon = 'audiobook'
        os.title_icon = dc.icon
        os.twit = os.title
        os.qrcode_url = '/cache/epub/%d/pg%d.qrcode.png' % (os.id, os.id)

        os.entries.append(dc)

        s = cherrypy.session
        last_visited = s.get('last_visited', [])
        last_visited.append(os.id)
        s['last_visited'] = last_visited

        # can we find some meaningful breadcrumbs ?
        for a in dc.authors:
            if a.marcrel in ('aut', 'cre'):
                book_cnt = BaseSearcher.sql_get(
                    "select count (*) from mn_books_authors where fk_authors = %(aid)s", aid = a.id)
                if book_cnt > 1:
                    os.breadcrumbs.append((
                        __('One by {author}', '{count} by {author}', book_cnt).format(
                                count = book_cnt, author = dc.make_pretty_name(a.name)),
                        _('Find more ebooks by the same author.'),
                         os.url('author', id = a.id)
                        ))


        if os.format == 'html':
            cat = BaseSearcher.Cat()
            cat.header = _('Similar Books')
            cat.title = _('Readers also downloaded…')
            cat.rel = 'related'
            cat.url = os.url('also', id = os.id)
            cat.class_ += 'navlink grayed noprint'
            cat.icon = 'suggestion'
            cat.order = 30
            os.entries.append(cat)

            for bookshelf in dc.bookshelves:
                cat = BaseSearcher.Cat()
                cat.title = _('In {bookshelf}').format(bookshelf = bookshelf.bookshelf)
                cat.rel = 'related'
                cat.url = os.url('bookshelf', id = bookshelf.id)
                cat.class_ += 'navlink grayed'
                cat.icon = 'bookshelf'
                cat.order = 33
                os.entries.append(cat)

        os.total_results = 1

        os.template = 'bibrec'
        os.page = 'bibrec'
        os.og_type = 'book'
        os.finalize()
        rendered = self.format(os)
        dc.session.close()
        return rendered
