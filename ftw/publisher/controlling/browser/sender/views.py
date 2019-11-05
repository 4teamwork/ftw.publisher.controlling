from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from ftw.publisher.controlling import _
from ftw.publisher.controlling.interfaces import IStatisticsCacheController
from ftw.publisher.sender.workflows import interfaces
from ftw.table.interfaces import ITableGenerator
from plone.protect import CheckAuthenticator
from plone.protect import PostOnly
from plone.protect import protect
from zope.component import getAdapters
from zope.component import getUtility
from zope.i18n import translate
import md5

try:
    from ftw.publisher.sender.interfaces import IConfig
except ImportError:
    SENDER_INSTALLED = False
else:
    SENDER_INSTALLED = True
    from ftw.publisher.sender.interfaces import IPathBlacklist


class ControllingView(BrowserView):
    """ Default publishment controlling view
    """

    def __call__(self):
        if self.request.get('form.selectrealm.submitted'):
            portal = self.context.portal_url.getPortalObject()
            controller = IStatisticsCacheController(portal)
            realm = self.get_realm_by_id(self.request.get('realm'))
            if not realm:
                raise Exception('Realm not found')
            controller.set_current_realm(realm)
            msg = _(u'info_selected_realm',
                    default=u'Realm selected')
            IStatusMessage(self.request).addStatusMessage(msg, type='info')
        return super(ControllingView, self).__call__()

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

    def get_realm_options(self):
        portal = self.context.portal_url.getPortalObject()
        config = IConfig(portal)
        controller = IStatisticsCacheController(portal)
        current_realm = controller.get_current_realm()
        for realm in config.getRealms():
            if realm.active:
                label = '%s : %s' % (realm.url, realm.username)
                yield {'id': self.make_realm_id(realm),
                       'label': label,
                       'selected': current_realm==realm,
                       }

    def make_realm_id(self, realm):
        return md5.md5('%s-%s' % (realm.url, realm.username)).hexdigest()

    def get_realm_by_id(self, id):
        config = IConfig(self.context.portal_url.getPortalObject())
        for realm in config.getRealms():
            if self.make_realm_id(realm)==id:
                return realm
        return None

    def last_updated(self):
        portal = self.context.portal_url.getPortalObject()
        controller = IStatisticsCacheController(portal)
        return controller.last_updated()


class RefreshStatistics(BrowserView):

    @protect(PostOnly)
    @protect(CheckAuthenticator)
    def __call__(self, REQUEST=None):
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

    template = ViewPageTemplateFile('element-listing.pt')

    def __call__(self):
        return self.template()

    def columns(self):
        return NotImplementedError

    def get_title(self):
        return NotImplementedError

    def get_elements_for_cache(self, controller):
        """ Calculates the elements for the cache. This method
        is called while the cache is refreshed.
        The result should only contain simple type objects such
        as string, list, dict, int etc.
        Use controller.get_remote_objects for getting remote objects
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

    def translate_workflow_state(self, workflow_id, state_id):
        wftool = getToolByName(self.context, 'portal_workflow')
        workflow = wftool.get(workflow_id)
        if not workflow:
            return state_id
        state = workflow.states.get(state_id)
        if state:
            return translate(state.title.decode('utf-8'),
                             domain='plone',
                             context=self.request).encode('utf-8')
        return state_id

    def translate_workflow_name(self, workflow_id):
        wftool = getToolByName(self.context, 'portal_workflow')
        workflow = wftool.get(workflow_id)
        if not workflow:
            return workflow_id
        return translate(workflow.title.decode('utf-8'),
                         domain='plone',
                         context=self.request).encode('utf-8')


class BrokenPublications(BaseStatistic):
    """ Show a list of all objects which are:
    - existing on the editing system
    - in a published state
    - not existing on the public system
    """

    def local_query(self):
        workflow_config_mappings = getAdapters(
            (self.request,),
            interfaces.IWorkflowConfiguration,
        )
        unpublished_states = []
        for workflow_config_mapping in workflow_config_mappings:
            workflow_config = workflow_config_mapping[1]
            for title, kind in workflow_config.lawgiver_states().items():
                if kind not in interfaces.PUBLISHED_STATES:
                    unpublished_states.append(
                        workflow_config._status_id(title)
                    )

        if unpublished_states:
            return {'review_state': unpublished_states}
        else:
            return {}

    def get_elements_for_cache(self, controller):
        bl = IPathBlacklist(self.context)
        for brain in self.context.portal_catalog(self.local_query()):
            if bl.is_blacklisted(brain):
                continue
            if controller.get_remote_item(brain=brain):
                yield {
                    'Title': brain.pretty_title_or_id(),
                    'path': brain.getPath(),
                    'review_state': self.translate_workflow_state(brain.workflow_id, brain.review_state),
                    'workflow_name': self.translate_workflow_name(brain.workflow_id),
                    'portal_type' : brain.portal_type,
                    }

    def get_title(self):
        return _(u'label_broken_publications',
                 default=u'Broken Publications')

    def columns(self):
        return ('Title',
                'portal_type',
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


class UnpublishedVisibles(BaseStatistic):
    """ Show a list of all objects wich are:
    - existing on the editing system but not in a public state
    - existing on the public system
    """

    def local_query(self):
        workflow_config_mappings = getAdapters(
            (self.request,),
            interfaces.IWorkflowConfiguration,
        )
        published_states = []
        for workflow_config_mapping in workflow_config_mappings:
            workflow_config = workflow_config_mapping[1]
            for title, kind in workflow_config.lawgiver_states().items():
                if kind in interfaces.PUBLISHED_STATES:
                    published_states.append(
                        workflow_config._status_id(title)
                    )

        if published_states:
            return {'review_state': published_states}
        else:
            return {}

    def get_elements_for_cache(self, controller):
        bl = IPathBlacklist(self.context)
        for brain in self.context.portal_catalog(self.local_query()):
            if bl.is_blacklisted(brain):
                continue
            ritem = controller.get_remote_item(brain=brain)
            if ritem and ritem['review_state'] != brain.review_state:
                yield {
                    'Title': brain.pretty_title_or_id(),
                    'path': brain.getPath(),
                    'review_state': self.translate_workflow_state(brain.workflow_id, brain.review_state),
                    'workflow_name': self.translate_workflow_name(brain.workflow_id),
                    'portal_type' : brain.portal_type,
                    }

    def get_title(self):
        return _(u'label_unpublished_visibles',
                 default=u'Unpublished visibles')

    def columns(self):
        return ('Title',
                'portal_type',
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


class NonExistingVisibles(BaseStatistic):
    """
    Show a list of objects wich are:
    - existing on the public system
    - but not existing on the editing system
    """

    def local_query(self):
        return {}

    def get_elements_for_cache(self, controller):
        """
        Get all remote objects and return those which
        do not existing locally.
        """
        remote_objects = controller.get_remote_objects()
        for item in remote_objects:
            local_path = controller.remote_to_local_path(item['path'])
            if not controller.get_local_brain(local_path):
                yield {
                    'Title': item['pretty_title_or_id'],
                    'path': item['getURL'],
                    'review_state': self.translate_workflow_state(item['workflow_id'], item['review_state']),
                    'workflow_name': self.translate_workflow_name(item['workflow_id']),
                    'portal_type': item['portal_type'],
                }

    def get_title(self):
        return _(u'label_non_existing_visibles',
                 default=u'Non-existing visibles')

    def columns(self):
        return ('Title',
                'portal_type',
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
