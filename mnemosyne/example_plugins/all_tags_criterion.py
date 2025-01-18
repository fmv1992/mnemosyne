from mnemosyne.libmnemosyne.plugin import Plugin
from mnemosyne.libmnemosyne.criterion import Criterion

import sys

import logging

print("B" * 790)
print("B" * 790, file=sys.stderr)
import os

# print(f"""{os.environ["PYTHONUNBUFFERED"]}""")


class HiGiver:
    def say_hi(self):
        print("hi")


class PrintMethodCalls:
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr):  # Check if the attribute is a method

            def wrapper(*args, **kwargs):
                print(f"Method called: {name}")
                return attr(*args, **kwargs)

            return wrapper
        return attr


class AllTagsCriterion(Criterion, PrintMethodCalls, HiGiver):
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


class AllTagsCriterionPlugin(Plugin, HiGiver):
    name = "All Tags Criterion"
    description = (
        "Adds a criterion that requires cards to have all specified tags"
    )
    components = [AllTagsCriterion]


from mnemosyne.libmnemosyne import Mnemosyne

mnemosyne = Mnemosyne(upload_science_logs=False, interested_in_old_reps=True)
AllTagsCriterion(mnemosyne).say_hi()
AllTagsCriterionPlugin(mnemosyne).say_hi()
