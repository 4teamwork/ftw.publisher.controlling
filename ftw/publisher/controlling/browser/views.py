from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.controlling import _
from ftw.publisher.controlling.interfaces import IStatisticsCacheController


class ControllingView(BrowserView):
    """ Default publishment controlling view
    """

    def get_actions(self):
        actions_tool = getToolByName(aq_inner(self.context), 'portal_actions')
        actions = actions_tool.listActionInfos(
            object=aq_inner(self.context),
            categories=('publisher_controlling_actions',))

        for action in actions:
            if action['allowed']:
                cssClass = 'publisher_controlling_actions-%s' % action['id']
                yield {'title': action['title'],
                       'description': action['description'],
                       'url': action['url'],
                       'selected': False,
                       'id': action['id'],
                       'class': cssClass,
                       }


class RefreshStatistics(BrowserView):

    def __call__(self):
        portal = self.context.portal_url.getPortalObject()
        controller = IStatisticsCacheController(portal)
        controller.rebuild_cache()
        message = _(u'info_refreshed_statistics',
                    default=u'Refreshed statistics successfully.')
        IStatusMessage(self.request).addStatusMessage(
            message,
            type='info'
            )
        return self.request.RESPONSE.redirect('@@publisher-controlling')


class BaseStatistic(BrowserView):
    """ Super class for statistics views
    """

    def get_elements_for_cache(self):
        """ Calculates the elements for the cache. This method
        is called while the cache is refreshed.
        The result should only contain simple type objects such
        as string, list, dict, int etc.
        """
        raise NotImplementedError

    def get_elements(self):
        """ Returns the cached elements. Returns
        an empty list if there are no elements cached yet.
        """
        portal = self.context.portal_url.getPortalObject()
        controller = IStatisticsCacheController(portal)
        return controller.get_elements_for(self.__name__, [])


class BrokenPublications(BaseStatistic):
    """ Show a list of all objects which are:
    - existing on the editing system
    - in a published state (see configuration in portal_properties)
    - not existing on the public system
    """

