# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009, Gustavo Narea <me@gustavonarea.net>.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Benchmark utilities for source adapters.

"""
from sys import platform
from time import clock, time

__all__ = ["AdapterBenchmark", "compare_benchmarks", "GroupsRetrievalAction",
           "PermissionsRetrievalAction"]


# http://coreygoldberg.blogspot.com/2008/09/python-timing-timeclock-vs-timetime.html
if platform == "win32":
    timer = clock
else:
    timer = time


class AdapterBenchmark(object):
    """
    Adapter benchmark.
    
    Instances of this class represent a benchmark on a :mod:`repoze.what`
    :term:`source adapter`.
    
    The source used by the adapter will be reset on every iteration, so if the
    adapter requires this to be handled in a special way, you should extend
    this class to override :meth:`reset_source` (but don't forget to call the
    original method).
    
    """
    
    def __init__(self, adapter):
        """
        Set up a benchmark for ``adapter``.
        
        :param adapter: The source adapter to be benchmarked.
        
        """
        self.adapter = adapter
    
    def run(self, action, iterations, source=None):
        """
        Return the time elapsed when ``action`` is run on the source adapter
        ``iterations`` times, with the adapter's source being reset to
        ``source`` on each iteration.
        
        :param action: The action to run on the adapter.
        :param iterations: The amount of times ``actions`` must be run.
        :type iterations: int
        :param source: The sections and items the source must contain.
        :type source: dict
        :return: The time elapsed, in seconds.
        :rtype: float
        
        The ``action`` is a callable that receives the adapter as the only
        argument.
        
        If ``source`` is ``None``, the source used by the adapter won't ever
        be reset.
        
        """
        elapsed_time = 0
        
        for iteration in range(iterations):
            self.reset_source(source)
            # Measuring the time:
            start_time = timer()
            action(self.adapter)
            end_time = timer()
            elapsed_time += end_time - start_time
            
        return elapsed_time
    
    def reset_source(self, source):
        """
        Reset the source used by the adapter to ``source`` if it's defined.
        
        :param source: The sections and items the source must contain.
        :type source: dict
        
        Either way, it will always reset the adapter's cache.
        
        """
        if source:
            # Emptying the adapter's source:
            sections = self.adapter.get_all_sections().keys()
            for section in sections:
                self.adapter.delete_section(section)
            # Filling the adapter's source:
            for (new_section, items) in source.items():
                self.adapter.create_section(new_section)
                self.adapter.set_section_items(new_section, items)
        # Resetting the adapter's cache:
        self.adapter.loaded_sections = {}
        self.adapter.all_sections_loaded = False


def compare_benchmarks(iterations, source, *actions, **benchmarks):
    """
    Compare all the ``benchmarks`` using the same criteria.
    
    :param iterations: How many times should each action in ``actions`` be
        executed.
    :type iterations: int
    :param source: The contents all the source adapters must have.
    :type source: dict
    :return: The results for each benchmark, organized by actions.
    :rtype: list
    :raises AssertionError: If there are no ``actions`` and/or less than 2
        ``benchmarks``.
    
    ``actions`` represent all the actions to be executed on each adapter.
    
    """
    assert len(actions) > 0, "At least one action must be run"
    assert len(benchmarks) > 1, "At least one benchmark must be specified"
    
    results = []
    
    for action in actions:
        action_results = {}
        for (benchmark_name, benchmark) in benchmarks.items():
            time_slapsed = benchmark.run(action, iterations, source)
            action_results[benchmark_name] = time_slapsed
        results.append(action_results)
    
    return results


#{ Built-in benchmark actions


class GroupsRetrievalAction(object):
    """
    Benchmark action that retrieves all the groups to which one user belongs.
    
    """
    
    def __init__(self, user_id):
        """Retrieve the groups for the user identified by ``user_id``."""
        self.user_id = user_id
    
    def __call__(self, adapter):
        credentials = {'repoze.what.userid': self.user_id}
        adapter.find_sections(credentials)


class PermissionsRetrievalAction(object):
    """
    Benchmark action that retrieves all the permissions granted to a given
    group.
    
    """
    
    def __init__(self, group_id):
        """Retrieve the permissions for the group identified by ``group_id``."""
        self.group_id = group_id
    
    def __call__(self, adapter):
        adapter.find_sections(self.group_id)


#}
