from time import monotonic

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Static, Label, Placeholder, TextLog

from tui_audiodisplay import TUIAudioDisplay
import csv
import io

from rich.table import Table
from rich.syntax import Syntax

from textual.app import App, ComposeResult
from textual import events
from textual.widgets import TextLog


CSV = """lane,swimmer,country,time
4,Joseph Schooling,Singapore,50.39
2,Michael Phelps,United States,51.14
5,Chad le Clos,South Africa,51.14
6,László Cseh,Hungary,51.14
3,Li Zhuhao,China,51.26
8,Mehdy Metella,France,51.58
7,Tom Shields,United States,51.73
1,Aleksandr Sadovnikov,Russia,51.84"""


CODE = '''\
def loop_first_last(values: Iterable[T]) -> Iterable[tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value\
'''

class KristaTUI(App):

    def __init__(self, state, tui_queue_in, tui_queue_out):
        super().__init__()
        #print("TUI Init")
        self.state = state
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out



        self.run()


    """A Textual app to manage stopwatches."""

    CSS_PATH = "krista_tui.css"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
    ]

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Container(Label("Keplermatik"), id="header_container")
        #yield Horizontal(Placeholder("abcd", id="left_map"), TUIAudioDisplay(id="map_container"), Placeholder("efgh", id="right_map"),id="asdas")
        yield Horizontal(Placeholder("abcd", id="left_map"), TextLog(highlight=True, markup=True), Placeholder("efgh", id="right_map"), id="asdas")
        yield Container(Placeholder("abcd", id="footer_container"))

    def on_ready(self) -> None:
        """Called  when the DOM is ready."""
        text_log = self.query_one(TextLog)

        text_log.write(Syntax(CODE, "python", indent_guides=True))

        rows = iter(csv.reader(io.StringIO(CSV)))
        table = Table(*next(rows))
        for row in rows:
            table.add_row(*row)

        text_log.write(table)
        text_log.write("[bold magenta]Write text or any Rich renderable!")

    def on_key(self, event: events.Key) -> None:
        """Write Key events to log."""
        text_log = self.query_one(TextLog)
        text_log.write(event)


