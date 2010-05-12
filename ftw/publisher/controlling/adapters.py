from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from datetime import datetime
from ftw.publisher.controlling.interfaces import IStatisticsCacheController
from ftw.publisher.controlling.utils import persistent_aware
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts

ANNOTATIONS_PREFIX = 'publisher-controlling-statistic-'
ANNOTATIONS_VERSION_KEY = 'publisher-controlling-version'
ANNOTATIONS_DATE_KEY = 'publisher-controlling-last-update'


class StatisticsCacheController(object):
    adapts(IStatisticsCacheController)

    def __init__(self, context):
        context = aq_inner(context)
        self.context = context
        self.portal = context.portal_url.getPortalObject()
        self.annotations = IAnnotations(self.portal)

    def rebuild_cache(self):
        """ Rebuilds the cache for each statistics view which
        is registered in portal_actions
        """
        for view in self._list_statistics_views():
            elements = view.get_elements_for_cache()
            self._store_elements_for(view.__name__, elements)
        self._increment_cache_version()
        self._set_last_update_date()

    def get_cache_version(self):
        """ The cache version is incremented after every successful
        update of the cache.
        """
        return int(self.annotations.get(ANNOTATIONS_VERSION_KEY, 0))

    def last_updated(self):
        """ Returns a datetime when the last successfull cache
        update happened.
        """
        return self.annotations[ANNOTATIONS_DATE_KEY]

    def get_elements_for(self, view_name, default=None):
        """ Returns the cached elements for a view (registered
        in portal_actions)
        """
        key = ANNOTATIONS_PREFIX + view_name
        return self.annotations.get(key, default)

    def _list_statistics_views(self):
        """ Returns a generator of views which are statistic views
        """
        actions_tool = getToolByName(aq_inner(self.context), 'portal_actions')
        actions = actions_tool.listActionInfos(
            object=aq_inner(self.context),
            categories=('publisher_controlling_actions',))

        for action in actions:
            if action['allowed']:
                url = action['url']
                url = url.endswith('/') and url[:-1] or url
                view_name = url.split('/')[-1]
                yield self.context.restrictedTraverse(view_name)


    def _store_elements_for(self, view_name, elements):
        """ Stores a list of elements for a view_name
        """
        key = ANNOTATIONS_PREFIX + view_name
        data = persistent_aware(elements)
        self.annotations[key] = data

    def _increment_cache_version(self):
        """ Increments the cache version
        """
        version = int(self.get_cache_version())
        version += 1
        self.annotations[ANNOTATIONS_VERSION_KEY] = version

    def _set_last_update_date(self):
        """ Sets the "last_updated" information to now
        """
        self.annotations[ANNOTATIONS_DATE_KEY] = datetime.now()

