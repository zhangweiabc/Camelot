#  ============================================================================
#
#  Copyright (C) 2007-2008 Conceptive Engineering bvba. All rights reserved.
#  www.conceptive.be / project-camelot@conceptive.be
#
#  This file is part of the Camelot Library.
#
#  This file may be used under the terms of the GNU General Public
#  License version 2.0 as published by the Free Software Foundation
#  and appearing in the file LICENSE.GPL included in the packaging of
#  this file.  Please review the following information to ensure GNU
#  General Public Licensing requirements will be met:
#  http://www.trolltech.com/products/qt/opensource.html
#
#  If you are unsure which license is appropriate for your use, please
#  review the following information:
#  http://www.trolltech.com/products/qt/licensing.html or contact
#  project-camelot@conceptive.be.
#
#  This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
#  WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#
#  For use of this library in commercial applications, please contact
#  project-camelot@conceptive.be
#
#  ============================================================================

"""Admin class for Plain Old Python Object
"""
import logging
logger = logging.getLogger('camelot.view.object_admin')

from camelot.view.model_thread import gui_function, model_function
from validator.object_validator import ObjectValidator


class ObjectAdmin(object):
  name = None
  list_display = []
  validator = ObjectValidator  
  fields = []
  form = [] #DEPRECATED
  form_display = []
  # list of field_names to filter on, if the field name is a one2many,
  # many2one or many2many field, the field name should be followed by a
  # field name of the related entity, eg : 'organization.name'
  list_filter = []
  list_charts = []
  list_actions = []
  list_search = []
  list_size = (600, 400)
  form_size = (700, 500)
  # Actions to be accessible by pushbuttons on the side of a form,
  # a list of tuples (button_label, action_function) where action_function
  # takes as its single argument, the object that is edited by the form
  # eg. : form_actions = [('Print', lamda o:print o)]
  form_actions = []
  form_title_column = None
  field_attributes = {}
  
  def __init__(self, app_admin, entity):
    """
    @param app_admin: the application admin object for this application
    @param entity: the entity class for which this admin instance is to be used
    """
    from camelot.view.remote_signals import get_signal_handler
    self.app_admin = app_admin
    self.rsh = get_signal_handler()
    if entity:
      from camelot.view.model_thread import get_model_thread
      self.entity = entity
      self.mt = get_model_thread()
    #
    # caches to prevent recalculation of things
    #
    self._field_attributes = dict()
    self._subclasses = None

  def __str__(self):
    return 'Admin %s' % str(self.entity.__name__)

  def getName(self):
    return (self.name or self.entity.__name__)

  def getModelThread(self):
    return self.mt

  @model_function
  def getFormActions(self, entity):
    return self.form_actions
  
  def getRelatedEntityAdmin(self, entity):
    """
    Get an admin object for another entity.  Taking into account preferences of this
    admin object or for those of admin object higher up the chain such as the
    application admin object.
    @param entity: the entity class for which an admin object is requested 
    """
    related_admin = self.app_admin.getEntityAdmin(entity)
    if not related_admin:
      logger.warn('no related admin found for %s'%(entity.__name__))
    return related_admin
  
  def getFieldAttributes(self, field_name):
    """
    Get the attributes needed to visualize the field field_name
    @param field_name : the name of the field
    @return: a dictionary of attributes needed to visualize the field, those
    attributes can be:
     * python_type : the corresponding python type of the object
     * editable : bool specifying wether the user can edit this field
     * widget : which widget to be used to render the field
     * ...
    """
    try:
      return self._field_attributes[field_name]
    except KeyError:
      from camelot.model.i18n import tr
      from camelot.view.controls import delegates
      #
      # Default attributes for all fields
      #
      attributes = dict(python_type=str,
                        length=None,
                        minimal_column_width=0,
                        editable=False,
                        nullable=True,
                        widget='str',
                        blank=True,
                        delegate=delegates.PlainTextColumnDelegate,
                        validator_list=[],
                        name=field_name.replace('_', ' ').capitalize())
      
      #
      # Field attributes forced by the field_attributes property
      #
      forced_attributes = {}
      try:
        forced_attributes = self.field_attributes[field_name]
      except KeyError:
        pass
      
      #
      # TODO : move part of logic from entity admin class over here
      #
      
      #
      # Overrule introspected field_attributes with those defined
      #
      attributes.update(forced_attributes)
      
      #
      # In case of a 'target' field attribute, instantiate an appropriate
      # 'admin' attribute
      #
      
      def get_entity_admin(target):
        """Helper function that instantiated an Admin object for a target entity class
        @param target: an entity class for which an Admin object is needed"""
        try:
          target = self.field_attributes[field_name].get('target', target)
          admin_class = self.field_attributes[field_name]['admin']
          return admin_class(self.app_admin, target)
        except KeyError:
          return self.getRelatedEntityAdmin(target)
        
      if 'target' in attributes:
        attributes['admin'] = get_entity_admin(attributes['target'])
      
      attributes['name'] = tr(attributes['name'])
      self._field_attributes[field_name] = attributes
      return attributes
    
      
  @model_function
  def getColumns(self):
    """
    The columns to be displayed in the list view, returns a list of pairs of
    the name of the field and its attributes needed to display it properly

    @return: [(field_name,
              {'widget': widget_type,
               'editable': True or False,
               'blank': True or False,
               'validator_list':[...],
               'name':'Field name'}),
             ...]
    """
    return [(field, self.getFieldAttributes(field))
            for field in self.list_display]

  def createValidator(self, model):
    return self.validator(self, model)
    
  @model_function
  def getFields(self):
    if self.form or self.form_display:
      fields = self.getForm().get_fields()
    elif self.fields:
      fields = self.fields
    else:
      fields = self.list_display
    fields_and_attributes =  [(field, self.getFieldAttributes(field)) for field in fields]
    return fields_and_attributes
  
  def getForm(self):
    from camelot.view.forms import Form, structure_to_form
    if self.form or self.form_display:
      return structure_to_form(self.form or self.form_display)
    return Form([f for f, a in self.getFields()])
  
  @gui_function
  def createFormView(self, title, model, index, parent):
    """Creates a Qt widget containing a form view, for a specific index in a
    model; uses the Admin class
    """
    logger.debug('creating form view for index %s' % index)
    from camelot.view.controls.formview import FormView
    form = FormView(title, self, model, index)
    return form
