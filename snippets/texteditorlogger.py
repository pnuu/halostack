import logging

class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super(Logger, self).__init__()

        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.textCursor().appendPlainText(msg)

    def write(self, m):
        pass

# Set up logging to use your widget as a handler
log_handler = QPlainTextEditLogger(<parent widget>)
logging.getLogger().addHandler(log_handler)
