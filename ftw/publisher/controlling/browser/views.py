from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.controlling import _
from ftw.publisher.controlling.interfaces import IStatisticsCacheController
from ftw.table.interfaces import ITableGenerator
from zope.component import getUtility


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

    def columns(self):
        return NotImplementedError

    def get_title(self):
        return NotImplementedError

    def get_elements_for_cache(self):
        """ Calculates the elements for the cache. This method
        is called while the cache is refreshed.
        The result should only contain simple type objects such
        as string, list, dict, int etc.
        """
        raise NotImplementedError

    def prepare_elements(self, elements):
        """ Used for updating the elements for rendering
        """
        return elements        

    def _get_elements(self):
        """ Returns the cached elements. Returns
        an empty list if there are no elements cached yet.
        """
        portal = self.context.portal_url.getPortalObject()
        controller = IStatisticsCacheController(portal)
        return controller.get_elements_for(self.__name__, [])

    def render(self):
        elements = self.prepare_elements(self._get_elements())
        generator = getUtility(ITableGenerator, 'ftw.tablegenerator')
        return generator.generate(elements, self.columns())



class BrokenPublications(BaseStatistic):
    """ Show a list of all objects which are:
    - existing on the editing system
    - in a published state (see configuration in portal_properties)
    - not existing on the public system
    """

    types = ['OrgUnit']
    states = ['published_internet']

    def get_elements_for_cache(self):
        query = {
            'portal_type': self.types,
            'review_state': self.states,
            }
        for brain in self.context.portal_catalog(query):
            yield {
                'Title': brain.Title,
                'path': brain.getPath(),
                'review_state': brain.review_state,
                'workflow_name': brain.workflow_name,
                }

    def get_title(self):
        return _(u'label_broken_publications',
                 default=u'Broken Publications')

    def columns(self):
        return ('Title',
                'review_state',
                'workflow_name',
                )

    def prepare_elements(self, elements):
        for elm in elements:
            elm['Title'] = '<a href="%s">%s</a>' % (
                elm['path'],
                elm['Title'],
                )
        return elements
