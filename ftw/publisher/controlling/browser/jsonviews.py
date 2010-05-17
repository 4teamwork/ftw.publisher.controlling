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
            'getPath',
            'review_state',
            'workflow_name',
            'UID',
            'portal_type',
            'start',
            'modified',
            'end',
            'expires',
            ]

    def additional_infos(self, brain, data):
        """ For adding additional, not attribute-based infos to
        the dict
        """
        return data

    def __call__(self):
        data = list(self._get_data())
        return simplejson.dumps(data)

    def _get_data(self):
        for brain in self.context.portal_catalog():
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
