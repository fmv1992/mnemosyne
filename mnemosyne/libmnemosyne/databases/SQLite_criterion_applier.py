#
# SQLite_criterion_applier.py <Peter.Bienstman@gmail.com>
#

from mnemosyne.libmnemosyne.criterion import CriterionApplier
from mnemosyne.libmnemosyne.criteria.default_criterion import (
    DefaultCriterion,
    TagMode,
)


class DefaultCriterionApplier(CriterionApplier):

    used_for = DefaultCriterion

    def split_set(self, _set, chunk_size):
        lst = list(_set)
        # Note that [1,2,3][2:666] = [3]
        return [
            lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)
        ]

    def set_activity_for_tags_with__id(self, _tag_ids, active):
        if len(_tag_ids) == 0:
            return
        command = """update cards set active=? where _id in
            (select _card_id from tags_for_card where _tag_id in ("""
        args = [1 if active else 0]
        for _tag_id in _tag_ids:
            command += "?,"
            args.append(_tag_id)
        command = command.rsplit(",", 1)[0] + "))"
        self.database().con.execute(command, args)

    def apply_to_database(self, criterion):
        db = self.database()
        tag_count = db.con.execute("select count() from tags").fetchone()[0]

        # fa804a3e-09aa-4dd8-9d98-e16d4d8dffe8: Handle different tag modes
        if criterion.tag_mode == TagMode.ANY:
            # Having any of these tags
            if len(criterion._tag_ids_active) == tag_count:
                # If every tag is active, take a shortcut
                db.con.execute("update cards set active=1")
            else:
                # Turn off everything first
                db.con.execute("update cards set active=0")
                # Turn on cards with any of the active tags
                for chunked__tag_ids in self.split_set(
                    criterion._tag_ids_active, 500
                ):
                    self.set_activity_for_tags_with__id(
                        chunked__tag_ids, active=1
                    )

        elif criterion.tag_mode == TagMode.NONE:
            # Not having any of these tags
            # Start with everything active
            db.con.execute("update cards set active=1")
            # Turn off cards with any forbidden tag
            for chunked__tag_ids in self.split_set(
                criterion._tag_ids_forbidden, 500
            ):
                self.set_activity_for_tags_with__id(chunked__tag_ids, active=0)

        elif criterion.tag_mode == TagMode.ALL:
            # Having all of these tags
            if not criterion._tag_ids_active:
                # If no tags are required, all cards are active
                db.con.execute("update cards set active=1")
            else:
                # Turn off everything first
                db.con.execute("update cards set active=0")
                # Get all cards that have tags
                card_ids = set()
                for (_card_id,) in db.con.execute(
                    "select distinct _card_id from tags_for_card"
                ):
                    card_ids.add(_card_id)

                # For each card, check if it has all required tags
                for _card_id in card_ids:
                    card_tag_ids = set()
                    for (_tag_id,) in db.con.execute(
                        """select _tag_id from
                        tags_for_card where _card_id=?""",
                        (_card_id,),
                    ):
                        card_tag_ids.add(_tag_id)

                    if criterion._tag_ids_active.issubset(card_tag_ids):
                        db.con.execute(
                            "update cards set active=1 where _id=?",
                            (_card_id,),
                        )

        # Turn off inactive card types and views
        if criterion.deactivated_card_type_fact_view_ids:
            command = "update cards set active=0 where "
            args = []
            for (
                card_type_id,
                fact_view_id,
            ) in criterion.deactivated_card_type_fact_view_ids:
                command += "(cards.fact_view_id=? and cards.card_type_id=?)"
                command += " or "
                args.append(fact_view_id)
                args.append(card_type_id)
            command = command.rsplit("or ", 1)[0]
            db.con.execute(command, args)
