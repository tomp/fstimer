#fsTimer - free, open source software for race timing.
#Copyright 2012-15 Ben Letham

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#The author/copyright holder can be contacted at bletham@gmail.com
'''Handling of the window dedicated to registration'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import fstimer.gui
import os
import re
from fstimer.gui.util_classes import MsgDialog
from fstimer.gui.util_classes import GtkStockButton

class RegistrationWin(Gtk.Window):
    '''Handling of the window dedicated to registration'''

    def __init__(self, path, fields, fieldsdic, prereg, projecttype,
            save_registration_cb, parent_win=None, autosave=True, save_label=''):
        '''Construct and display the registration window.'''
        super(RegistrationWin, self).__init__(Gtk.WindowType.TOPLEVEL)
        if parent_win:
            self.set_transient_for(parent_win)
            self.set_modal(True)
        self.project = os.path.basename(path)
        self.fields = fields
        self.fieldsdic = fieldsdic
        self.prereg = prereg
        self.ids = set()
        self.projecttype = projecttype
        self.save_registration_cb = save_registration_cb
        self.autosave = autosave
        self.editreg_win = None
        self.editregfields = None

        # First we define the registration model.
        # We will setup a liststore that is wrapped in a treemodelfilter
        # that is wrapped in a treemodelsort that is put in a treeview
        # that is put in a scrolled window. Eesh.
        self.regmodel = Gtk.ListStore(*[str for field in self.fields])
        self.modelfilter = self.regmodel.filter_new()
        self.modelfiltersorted = Gtk.TreeModelSort(self.modelfilter)
        self.treeview = Gtk.TreeView()

        # Now we define each column in the treeview
        for (colid, field) in enumerate(fields):
            column = Gtk.TreeViewColumn(field, Gtk.CellRendererText(), text=colid)
            column.set_sort_column_id(colid)
            self.treeview.append_column(column)

        # Now we populate the model with the pre-registration info, if any
        for reg in prereg:
            self.regmodel.append([reg[field] for field in fields])
            if reg['ID']:
                self.ids.add(reg['ID'])

        # This is the string that we filter based on.
        self.searchstr = ''
        self.modelfilter.set_visible_func(self.visible_filter)
        self.treeview.set_model(self.modelfiltersorted)
        self.treeview.set_enable_search(False)

        # Now let us actually build the window
        self.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        fname = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../data/icon.png'))
        self.set_icon_from_file(fname)
        self.set_title('fsTimer - ' + self.project)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('delete_event', lambda b, jnk: self.close_clicked(jnk))
        self.set_border_width(10)
        self.set_size_request(850, 450)

        #Now the filter entrybox
        filterbox = Gtk.HBox(False, 8)
        filterbox.pack_start(Gtk.Label('Filter by ', True, True, 0), False, False, 0)
        self.filter_combo = Gtk.ComboBoxText()
        for field in self.fields:
            self.filter_combo.append_text(field)
        self.filter_combo.set_active(0)
        filterbox.pack_start(self.filter_combo, False, False, 0)
        filterbox.pack_start(Gtk.Label(':'), False, False, 0)
        self.filterentry = Gtk.Entry()
        self.filterentry.set_max_length(40)
        self.filterentry.connect('changed', self.filter_apply)
        self.filterbtnCLEAR = GtkStockButton('clear',"Clear")
        self.filterbtnCLEAR.connect('clicked', self.filter_clear)
        self.filterbtnCLEAR.set_sensitive(False)
        filterbox.pack_start(self.filterentry, False, False, 0)
        filterbox.pack_start(self.filterbtnCLEAR, False, False, 0)

        # Now the scrolled window that contains the treeview
        regsw = Gtk.ScrolledWindow()
        regsw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        regsw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        regsw.add(self.treeview)

        # And a message that says if we have saved or not.
        self.regstatus = Gtk.Label(label=save_label)

        # Some boxes for all the stuff on the left
        regvbox1 = Gtk.VBox(False, 8)
        regvbox1.pack_start(filterbox, False, False, 0)
        regvbox1.pack_start(regsw, True, True, 0)
        regvbox1.pack_start(self.regstatus, False, False, 0)
        vbox1align = Gtk.Alignment.new(0, 0, 1, 1)
        vbox1align.add(regvbox1)

        # And boxes/table for the buttons on the right
        regtable = Gtk.Table(2, 1, False)
        regtable.set_row_spacings(5)
        regtable.set_col_spacings(5)
        regtable.set_border_width(5)

        btnEDIT = GtkStockButton('edit',"Edit")
        btnEDIT.connect('clicked', self.edit_clicked)

        btnREMOVE = GtkStockButton('remove',"Remove")
        btnREMOVE.connect('clicked', self.rm_clicked)

        btnNEW = GtkStockButton('new',"New")
        btnNEW.connect('clicked', self.new_clicked)

        btnSAVE = GtkStockButton('save',"Save")
        btnSAVE.connect('clicked', self.save_clicked)

        btnOK = GtkStockButton('close',"Close")
        btnOK.connect('clicked', self.close_clicked)

        vsubbox = Gtk.VBox(False, 8)
        vsubbox.pack_start(btnSAVE, False, False, 0)

        regvspacer = Gtk.Alignment.new(1, 1, 0, 0)
        regvspacer.add(vsubbox)
        regtable.attach(regvspacer, 0, 1, 1, 2)

        regvbox2 = Gtk.VBox(False, 8)
        regvbox2.pack_start(btnNEW, False, False, 0)
        regvbox2.pack_start(btnEDIT, False, False, 0)
        regvbox2.pack_start(btnREMOVE, False, False, 30)
        regvbalign = Gtk.Alignment.new(1, 0, 0, 0)
        regvbalign.add(regvbox2)
        regtable.attach(regvbalign, 0, 1, 0, 1)
        #Now we pack everything together
        reghbox = Gtk.HBox(False, 8)
        reghbox.pack_start(vbox1align, True, True, 0)
        reghbox.pack_start(regtable, False, False, 0)
        # Add in the close button on the bottom
        vbox_all = Gtk.VBox(False, 0)
        vbox_all.pack_start(reghbox, True, True, 0)
        donespacer = Gtk.Alignment.new(0, 0, 0, 0)
        donespacer.add(btnOK)
        vbox_all.pack_start(donespacer, False, False, 5)
        self.add(vbox_all)
        # And show.
        self.show_all()

    def visible_filter(self, model, titer, data):
        '''This is the filter function.
           It checks if self.searchstr is contained in column matching self.filter_combo
           case insensitive'''
        if self.searchstr:
            col_idx = self.filter_combo.get_active()
            if not model.get_value(titer, col_idx):
                return False
            else:
                return self.searchstr.lower() in model.get_value(titer, col_idx).lower()
        else:
            return True

    def filter_apply(self, jnk_unused):
        ''' handles modification of the content of the filter box
            sets self.searchstr to the current entrybox contents and refilter'''
        self.searchstr = self.filterentry.get_text()
        self.filterbtnCLEAR.set_sensitive(True)
        self.modelfilter.refilter()

    def filter_clear(self, jnk_unused):
        '''handles clearing of the filter box. Clears self.searchstr and refilter'''
        self.searchstr = ''
        self.filterentry.set_text('')
        self.filterbtnCLEAR.set_sensitive(False)
        self.modelfilter.refilter()

    def edit_clicked(self, jnk_unused):
        '''handles click on the 'edit' button on the registration window'''
        selection = self.treeview.get_selection()
        treeiter = selection.get_selected()[1]
        # if no selection, do nothing.
        if treeiter:
            # Grab the current information.
            current_info = {}
            for (colid, field) in enumerate(self.fields):
                current_info[field] = self.modelfiltersorted.get_value(treeiter, colid)
            # Find where this is in self.prereg
            preregiter = self.prereg.index(current_info)
            # Generate the window
            self.edit_registration(treeiter, preregiter, current_info)

    def rm_clicked(self, jnk_unused):
        '''Handling click on the 'remove' button of the registration window
           Throws up an 'are you sure' dialog box, and delete if yes'''
        selection = self.treeview.get_selection()
        treeiter = selection.get_selected()[1]
        # if nothing is selected, do nothing.
        if treeiter:
            rmreg_dialog = MsgDialog(self, 'warning', ['yes', 'no'], 'Really delete?', 'Are you sure you want to delete this entry?\nThis cannot be undone.')
            rmreg_dialog.set_default_response(Gtk.ResponseType.NO)
            response = rmreg_dialog.run()
            rmreg_dialog.destroy()
            if response == Gtk.ResponseType.YES:
                # Grab the current information.
                current_info = {}
                for (colid, field) in enumerate(self.fields):
                    current_info[field] = self.modelfiltersorted.get_value(treeiter, colid)
                # Find where this is in self.prereg
                preregiter = self.prereg.index(current_info)
                # converts the treeiter from sorted to filter to model, and remove
                self.regmodel.remove(self.modelfilter.convert_iter_to_child_iter(self.modelfiltersorted.convert_iter_to_child_iter(treeiter)))
                try:
                    self.ids.remove(current_info['ID'])
                except:
                    pass
                self.prereg.pop(preregiter)
                # The latest stuff has no longer been saved.
                self.regstatus.set_markup('')

    def new_clicked(self, jnk_unused):
        '''Handles click on the 'new' button on the registration window
           Creates the editreg window with a None treeiter and clear initial values.'''
        self.edit_registration(None, None, None)

    def save_clicked(self, jnk_unused):
        '''Handles click on the 'save' button on the registration window.
           We do a json dump of self.prereg'''
        filename, success = self.save_registration_cb()
        if success:
            self.regstatus.set_markup('<span color="blue">Registration saved to %s</span>' % filename)
            return True
        else:
            self.regstatus.set_markup('<span color="red">Registration NOT saved: %s</span>' % filename)
            return False

    def close_clicked(self, jnk_unused):
        '''Handles click on the 'close' button on the registration window.
           Throws up a 'do you want to save' dialog, and close the window'''
        okreg_dialog = MsgDialog(self, 'question', ['yes', 'no'], 'Save?', 'Do you want to save before finishing?\nUnsaved data will be lost.')
        okreg_dialog.set_default_response(Gtk.ResponseType.YES)
        response = okreg_dialog.run()
        okreg_dialog.destroy()
        if response == Gtk.ResponseType.YES:
            # this will save
            save_res = self.save_clicked(None)
            if not save_res:
                return
        self.hide()
        # Clear the file setting from pre-reg, in case pre-reg is
        # re-run without selecting a file
        del self.prereg[:]

    def edit_registration(self, treeiter, preregiter, current_info):
        '''handles creation/modification of a registration entry.
           Converts the treeiter from the treemodelsort to the liststore.'''
        if treeiter:
            treeiter = self.modelfilter.convert_iter_to_child_iter(self.modelfiltersorted.convert_iter_to_child_iter(treeiter))
        # Define the window
        self.editreg_win = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.editreg_win.modify_bg(Gtk.StateType.NORMAL, fstimer.gui.bgcolor)
        self.editreg_win.set_title('Registration entry')
        self.editreg_win.set_transient_for(self)
        self.editreg_win.set_modal(True)
        self.editreg_win.set_position(Gtk.WindowPosition.CENTER)
        self.editreg_win.connect('delete_event', lambda b, jnk_unused: self.editreg_win.hide())
        self.editreg_win.set_border_width(10)
        #An hbox for the buttons
        editreghbox = Gtk.HBox(False, 8)
        editregbtnOK = GtkStockButton('ok',"OK")
        editregbtnCANCEL = GtkStockButton('close',"Cancel")
        editregbtnCANCEL.connect('clicked', lambda b: self.editreg_win.hide())
        editreghbox.pack_start(editregbtnOK, False, False, 5)
        editreghbox.pack_start(editregbtnCANCEL, False, False, 5)
        # fill in current_info if available.
        self.editregfields = {}
        for field in self.fields:
            # Determine which type of entry is appropriate, create it and fill it.
            # Entrybox
            if self.fieldsdic[field]['type'] in ['entrybox', 'entrybox_int']:
                self.editregfields[field] = Gtk.Entry()
                self.editregfields[field].set_max_length(self.fieldsdic[field]['max'])
                if current_info:
                    self.editregfields[field].set_text(current_info[field])
            # Combobox
            elif self.fieldsdic[field]['type'] == 'combobox':
                self.editregfields[field] = Gtk.ComboBoxText()
                self.editregfields[field].append_text('')
                for val in self.fieldsdic[field]['options']:
                    self.editregfields[field].append_text(val)
                if current_info:
                    try:
                        indx = self.fieldsdic[field]['options'].index(current_info[field])
                        self.editregfields[field].set_active(indx+1)
                    except ValueError:
                        self.editregfields[field].set_active(0) #this catches if current_inf[field] is not a valid value. It is probably blank. Otherwise this is an issue, but we will force it blank.
                else:
                    self.editregfields[field].set_active(0)
        # Set up the vbox
        editregvbox = Gtk.VBox(False, 8)
        # We will make a smaller hbox for each of the fields.
        hboxes = {}
        for field in self.fields:
            hboxes[field] = Gtk.HBox(False, 15)
            hboxes[field].pack_start(Gtk.Label(field+':', True, True, 0), False, False, 0) #Pack the label
            hboxes[field].pack_start(self.editregfields[field], False, False, 0) #Pack the button/entry/..
            if self.projecttype == 'handicap' and field == 'Handicap':
                label_hd = Gtk.Label(label='hh:mm:ss')
                hboxes[field].pack_start(label_hd, False, False, 0)
            if field == 'ID':
                label_id = Gtk.Label('Must be unique')
                hboxes[field].pack_start(label_id, False, False, 0)
            editregvbox.pack_start(hboxes[field], False, False, 0) #Pack this hbox into the big vbox.
        #Pack and show
        if self.projecttype == 'handicap':
            editregbtnOK.connect('clicked', self.validate_entry, treeiter, preregiter, label_hd, label_id)
        else:
            editregbtnOK.connect('clicked', self.validate_entry, treeiter, preregiter, None, label_id)
        editregvbox.pack_start(editreghbox, False, False, 5)
        self.editreg_win.add(editregvbox)
        self.editreg_win.show_all()

    def validate_entry(self, jnk_unused, treeiter, preregiter, label_hd, label_id):
        '''Handles a click on the 'ok' button of the entry edition window.
           Reads out the input information, and writes the changes to the treemodel'''
        #First check if we have entered a handicap, and if so, make sure it is valid
        if self.projecttype == 'handicap':
            sduration = self.editregfields['Handicap'].get_text()
            if sduration != '':
                try:
                    timePattern = r'((?P<days>-?\d+) day(s)?, )?((?P<hours>\d+):)?'r'(?P<minutes>\d+):(?P<seconds>\d+)'
                    re.match(timePattern, sduration).groupdict(0)
                except AttributeError:
                    label_hd.set_markup('<span color="red">hh:mm:ss</span>')
                    return
        # If that was OK, we go through each field and grab the new value.
        new_vals = {}
        for field in self.fields:
            #Entrybox
            if self.fieldsdic[field]['type'] in ['entrybox', 'entrybox_int']:
                new_vals[field] = self.editregfields[field].get_text()
            #Combobox
            elif self.fieldsdic[field]['type'] == 'combobox':
                indx = self.editregfields[field].get_active()
                if indx == 0:
                    new_vals[field] = ''
                else:
                    new_vals[field] = self.fieldsdic[field]['options'][indx-1]
        # Make sure we don't have a duplicate ID, unless we are editing and leave it the same.
        if treeiter and new_vals['ID'] == self.prereg[preregiter]['ID']:
            pass  # No need for an ID check, it was already done.
        elif new_vals['ID'] in self.ids:
            label_id.set_markup('<span color="red">{} has already been used</span>'.format(new_vals['ID']))
            return
        # Now we replace or append in the treemodel and in prereg
        if treeiter:
            # Remove the old ID from the id store, and add the new value
            if self.prereg[preregiter]['ID']:
                self.ids.remove(self.prereg[preregiter]['ID'])
            # Update the tree and prereg
            for (colid, field) in enumerate(self.fields):
                self.regmodel.set_value(treeiter, colid, new_vals[field])
            self.prereg[preregiter] = new_vals
        else:
            self.regmodel.append([new_vals[field] for field in self.fields])
            self.prereg.append(new_vals)
        # Add the new ID to the id store
        if new_vals['ID']:
            self.ids.add(new_vals['ID'])
        # The saved status is unsaved
        self.regstatus.set_markup('')
        # Filter results by the current filter field, for this value
        self.filterentry.set_text(new_vals[self.filter_combo.get_active_text()])
        # Save
        if self.autosave:
            self.save_clicked(None)
        # we're done
        self.editreg_win.hide()
