from PyQt6 import QtWidgets

from mnemosyne.libmnemosyne.plugin import Plugin
from mnemosyne.libmnemosyne.criterion import Criterion
from mnemosyne.libmnemosyne.gui_translator import _
from mnemosyne.libmnemosyne.ui_components.criterion_widget import (
    CriterionWidget,
)
from mnemosyne.pyqt_ui.tag_tree_wdgt import TagsTreeWdgt
from mnemosyne.pyqt_ui.card_type_tree_wdgt import CardTypesTreeWdgt


class AllTagsCriterion(Criterion):
    criterion_type = "all_tags"

    def __init__(self, component_manager, id=None):
        Criterion.__init__(self, component_manager, id)
        self.deactivated_card_type_fact_view_ids = set()
        self._tag_ids_required = set()
        self._tag_ids_forbidden = set()

    def apply_to_card(self, card):
        card.active = True
        # Check if all required tags are present
        for required_tag_id in self._tag_ids_required:
            tag_found = False
            for card_tag in card.tags:
                if card_tag._id == required_tag_id:
                    tag_found = True
                    break
            if not tag_found:
                card.active = False
                break

        # Check card type deactivation
        if (
            card.card_type.id,
            card.fact_view.id,
        ) in self.deactivated_card_type_fact_view_ids:
            card.active = False

        # Check forbidden tags
        for tag in card.tags:
            if tag._id in self._tag_ids_forbidden:
                card.active = False
                break

    def active_tag_added(self, tag):
        self._tag_ids_required.add(tag._id)

    def deactivated_tag_added(self, tag):
        if len(self._tag_ids_forbidden) != 0:
            self._tag_ids_forbidden.add(tag._id)

    def is_tag_active(self, tag):
        return tag._id in self._tag_ids_required

    def tag_deleted(self, tag):
        self._tag_ids_required.discard(tag._id)
        self._tag_ids_forbidden.discard(tag._id)

    def data_to_string(self):
        return repr(
            (
                self.deactivated_card_type_fact_view_ids,
                self._tag_ids_required,
                self._tag_ids_forbidden,
            )
        )

    def set_data_from_string(self, data_string):
        data = eval(data_string)
        self.deactivated_card_type_fact_view_ids = data[0]
        self._tag_ids_required = data[1]
        self._tag_ids_forbidden = data[2]

    def data_to_sync_string(self):
        required_tag_ids = set()
        for _tag_id in self._tag_ids_required:
            tag = self.database().tag(_tag_id, is_id_internal=True)
            required_tag_ids.add(tag.id)
        forbidden_tag_ids = set()
        for _tag_id in self._tag_ids_forbidden:
            tag = self.database().tag(_tag_id, is_id_internal=True)
            forbidden_tag_ids.add(tag.id)
        return repr(
            (
                self.deactivated_card_type_fact_view_ids,
                required_tag_ids,
                forbidden_tag_ids,
            )
        )

    def set_data_from_sync_string(self, data_string):
        data = eval(data_string)
        self.deactivated_card_type_fact_view_ids = data[0]
        required_tag_ids = data[1]
        forbidden_tag_ids = data[2]
        self._tag_ids_required = set()
        for tag_id in required_tag_ids:
            tag = self.database().tag(tag_id, is_id_internal=False)
            self._tag_ids_required.add(tag._id)
        self._tag_ids_forbidden = set()
        for tag_id in forbidden_tag_ids:
            tag = self.database().tag(tag_id, is_id_internal=False)
            self._tag_ids_forbidden.add(tag._id)


class AllTagsCriterionWdgt(QtWidgets.QWidget, CriterionWidget):
    used_for = AllTagsCriterion

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.parent = kwds["parent"]
        self.component_manager = kwds["component_manager"]
        self.layout = QtWidgets.QGridLayout(self)

        # Card types section
        self.card_type_label = QtWidgets.QLabel(self)
        self.card_type_label.setText(
            _("Activate cards from these card types:")
        )
        self.layout.addWidget(self.card_type_label, 0, 0)

        self.card_type_tree_wdgt = CardTypesTreeWdgt(
            component_manager=self.component_manager, parent=self
        )
        self.layout.addWidget(self.card_type_tree_wdgt, 1, 0)

        # Tags section
        self.tag_label = QtWidgets.QLabel(self)
        self.tag_label.setText(_("Having all of these tags:"))
        self.layout.addWidget(self.tag_label, 0, 1)

        self.tag_tree_wdgt = TagsTreeWdgt(
            component_manager=self.component_manager, parent=self
        )
        self.layout.addWidget(self.tag_tree_wdgt, 1, 1)

        # Initialize with all tags active
        criterion = AllTagsCriterion(component_manager=self.component_manager)
        for tag in self.database().tags():
            criterion._tag_ids_required.add(tag._id)
        self.display_criterion(criterion)

        # Connect signals
        self.card_type_tree_wdgt.tree_wdgt.itemChanged.connect(
            self.criterion_changed
        )
        self.tag_tree_wdgt.tree_wdgt.itemChanged.connect(
            self.criterion_changed
        )
        self.card_type_tree_wdgt.tree_wdgt.itemClicked.connect(
            self.criterion_clicked
        )
        self.tag_tree_wdgt.tree_wdgt.itemClicked.connect(
            self.criterion_clicked
        )

    def display_criterion(self, criterion):
        self.card_type_tree_wdgt.display(criterion)
        self.tag_tree_wdgt.display(criterion)

    def criterion(self):
        criterion = AllTagsCriterion(component_manager=self.component_manager)
        criterion = self.card_type_tree_wdgt.checked_to_criterion(criterion)
        self.tag_tree_wdgt.checked_to_active_tags_in_criterion(criterion)
        return criterion

    def criterion_clicked(self):
        if (
            self.parent.was_showing_a_saved_set
            and not self.parent.is_shutting_down
        ):
            self.main_widget().show_information(
                _(
                    "Cards you (de)activate now will not be stored in the previously selected set unless you click 'Save this set for later use' again. This allows you to make some quick-and-dirty modifications."
                )
            )
            self.parent.was_showing_a_saved_set = False

    def criterion_changed(self):
        self.parent.saved_sets.clearSelection()

    def closeEvent(self, event):
        self.tag_tree_wdgt.close()


class AllTagsCriterionPlugin(Plugin):
    name = "All Tags Criterion"
    description = (
        "Adds a criterion that requires cards to have all specified tags"
    )
    components = [AllTagsCriterion, AllTagsCriterionWdgt]
