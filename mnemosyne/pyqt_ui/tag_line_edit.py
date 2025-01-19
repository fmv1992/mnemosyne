#
# tag_line_edit.py Emilian Mihalache <emihalac@gmail.com>
#

from PyQt6 import QtCore, QtWidgets
from mnemosyne.pyqt_ui.tag_completer import TagCompleter


class TagLineEdit(QtWidgets.QLineEdit):

    completion_prefix_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(TagLineEdit, self).__init__(parent)

        # Stored because when we get the 'activated' signal,
        # the cursor has already moved at the end of the lineedit.
        # This can be jarring to the user if they are inserting
        # a tag in the middle of the text.
        self.last_cursor_position_ = 0
        # Stored because the popup list generated by the completer
        # tends to report the wrong index when emitting activated().
        # Debugging this lead nowhere, so let's just treat the last
        # highlighted item as the completion when we get the 'activated'
        # signal.
        self.last_highlight_ = ""

        self.custom_completer_ = TagCompleter(self)
        self.custom_completer_.setWidget(self)

        self.textEdited.connect(self.self_text_changed)
        self.completion_prefix_changed.connect(
            self.custom_completer_.handle_prefix_change
        )
        self.custom_completer_.activated[str].connect(self.fill_in_completion)
        self.custom_completer_.highlighted[str].connect(
            self.handle_completer_highlight_
        )

    def handle_completer_highlight_(self, text):
        self.last_highlight_ = text
        self.last_cursor_position_ = self.cursorPosition()

    def fill_in_completion(self, completion):
        # 'completion' is intentionally discarded due to often being
        # erroneously reported by the Qt popup. Last highlighted suggestion
        # is used instead.
        old_text = self.text()
        cursor_position = self.last_cursor_position_
        previous_comma_index = old_text[:cursor_position].rfind(",") + 1

        new_text = (
            old_text[:previous_comma_index]
            + self.last_highlight_
            + ","
            + old_text[cursor_position:]
        )
        self.setText(new_text)
        new_cursor_index = previous_comma_index + len(self.last_highlight_)
        self.setCursorPosition(
            previous_comma_index + len(self.last_highlight_) + 1
        )

    def refresh_completion_model(self, new_model):
        self.custom_completer_.refresh_completion_model(new_model)

    def self_text_changed(self, new_text):
        self.completion_prefix_changed.emit(self.last_tag_prefix(new_text))

    def last_tag_prefix(self, text):
        cursor_position = self.cursorPosition()
        last_relevant_comma_index = text[0:cursor_position].rfind(",")
        return text[last_relevant_comma_index + 1 : cursor_position].strip()
