#  ============================================================================
#
#  Copyright (C) 2007-2012 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file license.txt included in the packaging of
#  this file.  Please review this information to ensure GNU
#  General Public Licensing requirements will be met.
#
#  If you are unsure which license is appropriate for your use, please
#  visit www.python-camelot.com or contact project-camelot@conceptive.be
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from customeditor import CustomEditor, set_background_color_palette, draw_tooltip_visualization
import re

class PartEditor(QtGui.QLineEdit):

    def __init__(self, mask, max_length, first = False, last = False):
        super(PartEditor, self).__init__()
        self.setInputMask(mask)
        self.firstPart = first
        self.last = last
        self.max_length = max_length
        self.textEdited.connect( self.text_edited )

    def focusInEvent(self, event):
        super(PartEditor, self).focusInEvent(event)
        self.setCursorPosition(0)
        
    def focusOutEvent(self, event):
        super(PartEditor, self).focusOutEvent(event)
        if self.isModified():
            self.editingFinished.emit()
        
    def paintEvent(self, event):
        super(PartEditor, self).paintEvent(event)
        if self.firstPart and self.toolTip():
            draw_tooltip_visualization(self)

    @QtCore.pyqtSlot(str)
    def text_edited(self, text):
        if self.cursorPosition() == self.max_length:
            if self.last:
                self.editingFinished.emit()
            else:
                self.focusNextChild()
        
class CodeEditor(CustomEditor):

    def __init__(self, parent=None, parts=['99','AA'], editable=True, field_name='code', **kwargs):
        CustomEditor.__init__(self, parent)
        self.setObjectName( field_name )
        self.parts = parts
        self.part_editors = []
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)
        for i, part in enumerate(parts):
            part = re.sub('\W*', '', part)
            part_length = len(part)
            editor = PartEditor(part, part_length, i==0, i==(len(parts)-1) )
            editor.setFocusPolicy( Qt.StrongFocus )
            if i==0:
                self.setFocusProxy( editor )
            if not editable:
                editor.setEnabled(False)
            space_width = editor.fontMetrics().size(Qt.TextSingleLine, 'A').width()
            editor.setMaximumWidth(space_width*(part_length+1))
            self.part_editors.append(editor)
            layout.addWidget(editor)
            editor.editingFinished.connect(self.emit_editing_finished)
        self.setLayout(layout)

    @QtCore.pyqtSlot()
    def emit_editing_finished(self):
        # if we don't do an isModified check here, spurious editingFinished
        # signals are generated by the QLineEdit itself, maybe because of the
        # pattern.  this can lead to spurious data entry in a form, therefor this
        # check is necessary
        for editor in self.part_editors:
            if editor.isModified():
                self.editingFinished.emit()
                return

    def set_enabled(self, editable=True):
        for editor in self.part_editors:
            editor.setEnabled(editable)

    def set_value(self, value):
        value = CustomEditor.set_value(self, value)
        if value:
            old_value = self.get_value()
            if value!=old_value:
                for part_editor, part in zip(self.part_editors, value):
                    part_editor.setText(unicode(part))
        else:
            for part_editor in self.part_editors:
                part_editor.setText('')

    def get_value(self):
        value = []
        for part in self.part_editors:
            value.append(unicode(part.text()))
        return CustomEditor.get_value(self) or value

    def set_background_color(self, background_color):
        for editor in self.part_editors:
            set_background_color_palette( editor, background_color )
            
    def set_field_attributes(self, editable = True,
                                   background_color = None,
                                   tooltip = None, **kwargs):
        self.set_enabled(editable)
        self.set_background_color(background_color)
        self.layout().itemAt(0).widget().setToolTip(unicode(tooltip or ''))

