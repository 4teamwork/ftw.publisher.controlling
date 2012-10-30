from Products.CMFCore.utils import getToolByName
from plone.indexer.decorator import indexer
from zope.interface import Interface


@indexer(Interface)
def workflow_name(obj):
    """Workflow name indexer.
    """
    wf_tool = getToolByName(obj, 'portal_workflow')
    workflows = wf_tool.getWorkflowsFor(obj)

    if len(workflows) > 0:
        return wf_tool.getWorkflowsFor(obj)[0].id
    else:
        return None
