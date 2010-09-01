'''
Wizard to merge documents with a list of objects.

This wizard is triggered thru an entry in the main menu.
'''

from PyQt4 import QtGui

from camelot.core.utils import ugettext_lazy as _
from camelot.view.art import Icon
from camelot.view.wizard.pages.progress_page import ProgressPage
from camelot.view.wizard.pages.select import SelectFilePage

class SelectTemplatePage(SelectFilePage):
    """Page to select the template to merge"""
    title = _('Merge a template document')
    sub_title = _(
        "Click 'Browse' to select a template file, then click 'Next'."
    )
    icon = Icon('tango/32x32/mimetypes/x-office-document-template.png')

class MergePage(ProgressPage):
    """Wait until merge is complete"""
    title = _('Merge in progress')
    
    def __init__(self, parent, selection_getter):
        super(MergePage, self).__init__(parent)
        self._selection_getter = selection_getter

class MergeDocumentWizard(QtGui.QWizard):
    """This wizard lets the user select a template file, it then
merges that template will all the selected rows in a table"""
    
    window_title = _('Merge Document')

    def __init__(self, parent=None, selection_getter=None):
        """:param selection_getter: function to loop over the list of objects
        to merge"""
        super(MergeDocumentWizard, self).__init__(parent)
        self.setWindowTitle( unicode(self.window_title) )
        assert selection_getter
        self.addPage(SelectTemplatePage(parent=self))
        self.addPage(MergePage(parent=self, selection_getter=selection_getter))
