from DateTime import DateTime
from Products.Five import BrowserView
import simplejson


class ListRemoteObjects(BrowserView):
    """ Returns a json-formatted list of some basic infos of any
    object in the catalog.
    """

    def attributes(self):
        """ Returns a list of attribtues which are returned (from the brain).
        If an attribute is callable it will be called.
        """
        return [
            'Title',
            'review_state',
            'UID',
            'portal_type',
            'start',
            'modified',
            'end',
            'expires',
            'absolute_url',
            ]

    def additional_infos(self, brain, data):
        """ For adding additional, not attribute-based infos to
        the dict
        """
        path = brain.getPath()
        if not path.startswith(self.portal_path):
            raise Exception('path of %s does not start as expected: %s' % (
                    `brain`,
                    path
                    ))
        data['path'] = path[len(self.portal_path):]
        return data

    def __call__(self):
        self.portal_path = '/'.join(self.context.portal_url.getPortalObject().getPhysicalPath())+'/'
        data = list(self._get_data())
        return simplejson.dumps(data)

    def _get_data(self):
        for brain in self.context.portal_catalog(path={
                'query': '/zug.ch/www.zug.ch/organisation',
                'limit': 0,
                }):
            yield self._get_brain_data(brain)

    def _get_brain_data(self, brain):
        data = {}
        for name in self.attributes():
            value = getattr(brain, name, None)
            if not value and `value`=='Missing.Value':
                value = None
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    pass
            if isinstance(value, DateTime):
                value = value.ISO8601()
            data[name] = value
        return self.additional_infos(brain, data)
