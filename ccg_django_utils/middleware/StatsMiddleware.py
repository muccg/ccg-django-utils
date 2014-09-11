# -*- coding: utf-8 -*-

from operator import add
from time import time
from django.db import connection
import logging
from functools import reduce
logger = logging.getLogger('stats')

class StatsMiddleware(object):

    #config options
    LOG_HANDLER_NAME = __name__ 
    LOG_AJAX_ONLY = False
    PATH_WHITELIST = [] #no entries means log everything


    def is_matching_path(self, path):
        matching_path = False
        num_paths = len(self.PATH_WHITELIST)
        if num_paths > 0:
            count = 0
            while matching_path is False and count < num_paths:
                if self.PATH_WHITELIST[count] in path:
                    matching_path = True
                count += 1
        else:
            matching_path = True
        return matching_path

    def process_view(self, request, view_func, view_args, view_kwargs):
        # turn on debugging in db backend to capture time
        from django.conf import settings
        if hasattr(settings, 'STATS_MIDDLEWARE_LOGGER'):
            self.LOG_HANDLER_NAME = settings.STATS_MIDDLEWARE_LOGGER
        if hasattr(settings, 'STATS_MIDDLEWARE_LOG_AJAX_ONLY'):    
            self.LOG_AJAX_ONLY = settings.STATS_MIDDLEWARE_LOG_AJAX_ONLY
        if hasattr(settings, 'STATS_MIDDLEWARE_PATH_WHITELIST'):    
            self.PATH_WHITELIST = settings.STATS_MIDDLEWARE_PATH_WHITELIST


        logger = logging.getLogger(self.LOG_HANDLER_NAME)
        
        path = request.META.get('PATH_INFO', 'Unknown')
        ajax = request.META.get('HTTP_X_REQUESTED_WITH', False) == 'XMLHttpRequest'

        should_log = False

        #if LOG_AJAX_ONLY is true and this is an ajax request, OR if LOG_AJAX_ONLY is false (we dont care)
        #AND
        #if either the path whitelist is empty, OR our path contains one of the whitelist entries,
        #then do all this stuff.

        if ( (self.LOG_AJAX_ONLY and ajax) or (self.LOG_AJAX_ONLY is False) ) and self.is_matching_path(path):
            should_log = True

        if settings.DEBUG:
            # get number of db queries before we do anything
            n = len(connection.queries)
        else:
            n = 0
        # time the view
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        totTime = time() - start
        dbTime = 0.0
        queries = 0
        if settings.DEBUG:
            # compute the db time for the queries just run
            queries = len(connection.queries) - n
            if queries:
                dbTime = reduce(add, [float(q['time']) 
                                    for q in connection.queries[n:]])

        pyTime = totTime - dbTime

        stats = {
            'totTime': totTime,
            'pyTime': pyTime,
            'dbTime': dbTime,
            'queries': queries,
            'sql': connection.queries
            }

        if should_log:
            if settings.DEBUG:
                logger.debug("Path:%s, AJAX:%s, Total:%.2f, Py:%2f, DB:%2f (%d)" % (path, ajax, stats['totTime'], stats['pyTime'], stats['dbTime'], stats['queries']) )
            else:
                logger.debug("Path:%s, AJAX:%s, Total:%.2f" % (path, ajax, stats['totTime']) )
        
        return response

