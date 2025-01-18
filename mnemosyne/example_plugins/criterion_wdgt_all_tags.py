from PyQt6 import QtCore, QtGui, QtWidgets

from mnemosyne.libmnemosyne.gui_translator import _
from mnemosyne.libmnemosyne.ui_components.criterion_widget import CriterionWidget
from mnemosyne.example_plugins.all_tags_criterion import AllTagsCriterion
from mnemosyne.pyqt_ui.tag_tree_wdgt import TagsTreeWdgt
from mnemosyne.pyqt_ui.card_type_tree_wdgt import CardTypesTreeWdgt

class AllTagsCriterionWdgt(QtWidgets.QWidget, CriterionWidget):
    """Widget for selecting tags that must all be present on cards."""

    component_type = "criterion_widget"
    used_for = AllTagsCriterion

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.parent = kwds["parent"]
        self.component_manager = kwds["component_manager"]
        
        # Create layout
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Add card type tree
        self.card_type_tree_wdgt = CardTypesTreeWdgt(
            component_manager=self.component_manager, parent=self)
        self.layout.addWidget(QtWidgets.QLabel(_("Activate cards from these card types:")))
        self.layout.addWidget(self.card_type_tree_wdgt)
        
        # Add tag tree
        self.tag_tree_wdgt = TagsTreeWdgt(
            component_manager=self.component_manager, parent=self)
        self.layout.addWidget(QtWidgets.QLabel(_("Cards must have ALL these tags:")))
        self.layout.addWidget(self.tag_tree_wdgt)
        
        # Connect signals
        self.card_type_tree_wdgt.tree_wdgt.itemChanged.connect(self.criterion_changed)
        self.tag_tree_wdgt.tree_wdgt.itemChanged.connect(self.criterion_changed)
        self.card_type_tree_wdgt.tree_wdgt.itemClicked.connect(self.criterion_clicked)
        self.tag_tree_wdgt.tree_wdgt.itemClicked.connect(self.criterion_clicked)

    def display_criterion(self, criterion):
        """Display the criterion settings in the widget."""
        self.card_type_tree_wdgt.display(criterion)
        self.tag_tree_wdgt.display(criterion)

    def criterion(self):
        """Build criterion from the widget state."""
        criterion = AllTagsCriterion(component_manager=self.component_manager)
        criterion = self.card_type_tree_wdgt.checked_to_criterion(criterion)
        self.tag_tree_wdgt.checked_to_active_tags_in_criterion(criterion)
        return criterion

    def criterion_clicked(self):
        if self.parent.was_showing_a_saved_set and not self.parent.is_shutting_down:
            self.main_widget().show_information(
                _("Cards you (de)activate now will not be stored in the previously selected set unless you click 'Save this set for later use' again. This allows you to make some quick-and-dirty modifications."))
            self.parent.was_showing_a_saved_set = False

    def criterion_changed(self):
        self.parent.saved_sets.clearSelection()

    def closeEvent(self, event):
        self.tag_tree_wdgt.close()