import asyncio
import warnings
from time import monotonic

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Header, Footer, Static, Label, Placeholder, TextLog, Input

from tui_audiodisplay import TUIAudioDisplay
import csv
import io

from rich.table import Table
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.json import JSON
from rich.text import Text
import textwrap


from textual.app import App, ComposeResult
from textual import events
from textual.widgets import TextLog

from krista_util import IPCMessage

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
class ListenWidget(Static):
    def __init__(self, message,
                 name: str | None = None,
                 id: str | None = None,
                 classes: str | None = None, ):
        super().__init__(name=name, id=id, classes=classes)
        self._spinner = Spinner("dots8", message)



    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 60, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(self._spinner)

class TranscribeWidget(Static):
    def __init__(self, message,
                 name: str | None = None,
                 id: str | None = None,
                 classes: str | None = None, ):
        super().__init__(name=name, id=id, classes=classes)
        self._spinner = Spinner("dots8", message)



    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 60, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(self._spinner)


class KristaTUI(App):

    def __init__(self, state, tui_queue_in, tui_queue_out, transcription_queue):
    #def __init__(self):
        super().__init__()
        #print("TUI Init")
        self.state = state
        self.tui_queue_in = tui_queue_in
        self.tui_queue_out = tui_queue_out
        self.transcription_queue = transcription_queue

        self.chat_log_content = ""
        self.json_log_content = ""


        self.run()


    """A Textual app to manage stopwatches."""

    CSS_PATH = "krista_tui.css"

    BINDINGS = [
        ("`", "focus_input", "Chat"),
    ]


    def action_focus_input(self) -> None:
        input_box = self.query_one("#chat_input")
        self.screen.set_focus(input_box)

    def compose(self) -> ComposeResult:
        self.listen_status = Label("Listen", id="listen_status")
        self.transcriber_status = Label("Transcribe", id="transcriber_status")
        self.agent_status = Label("Agent", id="agent_status")

        #chat_log = TextLog(highlight=False, markup=True, wrap=False, id="chat_log")
        #json_log = TextLog(highlight=False, markup=True, wrap=True, id="json_log")
        chat_log = Static(id="chat_log")
        json_log = Static(id="json_log")


        """Called to add widgets to the app."""
        yield Horizontal(Label(":ringed_planet: Keplermatik Krista"), id="header_container")
        yield Horizontal(Label("audio stuff", id="audio_stats"), TUIAudioDisplay(id="fft_container"), id="audio_container")
        yield Horizontal(Vertical(Label(" Chat"), chat_log, Horizontal(Label("\n Input "), Input(placeholder = "", id="chat_input"), id="input_container"), id="chat_container"), Vertical(Label(" Generated JSON"), json_log, id="json_container"), id="logs")
        yield Horizontal(Label("Raw transcription: ", id="raw_transcription_label"), Static("", id="transcription_message"), id="status_container")
        yield Horizontal(self.listen_status, Label(" | ", classes="seperator"), self.transcriber_status, Label(" | ", classes="seperator"), self.agent_status, id="footer_container")

    def on_ready(self) -> None:
        """Called  when the DOM is ready."""
        chat_log = self.query_one("#chat_log")

        json_log = self.query_one("#json_log")
        self.listen_status.styles.color = "red"

        asyncio.get_event_loop().create_task(self.get_messages())

        #chat_log.write("[bold white]Krista:  Hi!  I'm Krista!  What can I help you with?")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """A coroutine to handle a text changed message."""
        if message.value:
            # Look up the word in the background
            # self.query_one("#chat_log").write("[bold red]You:")
            # self.query_one("#chat_log").write(str(message.value))
            # self.query_one("#chat_log").write(" ")

            self.chat_log_content = "" + "[bold red]You:\n[white]" + message.value + "\n"
            self.query_one("#chat_log").update(self.chat_log_content)

            ipc_message = IPCMessage("TRANSCRIPTION", message.value)
            self.transcription_queue.put(ipc_message)

            self.query_one("#chat_input").value = ""



    # def on_key(self, event: events.Key) -> None:
    #     """Write Key events to log."""
    #     text_log = self.query_one("#chat_log")
    #     text_log.write(event)


    async def get_messages(self):
        while 1:

#            self.query_one("#chat_log").write("test")
            warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

            while not self.tui_queue_in.empty():
                ipc_message = self.tui_queue_in.get()

                if ipc_message.type == "AGENT_MESSAGE":
                    self.chat_log_content += "\n" + "[bold blue]Krista:\n[white]" + ipc_message.data
                    self.query_one("#chat_log").update(self.chat_log_content)
                    self.chat_log_content = ""


                if ipc_message.type == "JSON_MESSAGE":
                    self.json_log_content = ipc_message.data

                    #self.query_one("#json_log").update(Syntax(self.json_log_content, "json", background_color="#181414", indent_guides=False))
                    self.query_one("#json_log").update(JSON(self.json_log_content))
                    #self.query_one("#json_log").update(ipc_message.data)
                    # self.query_one("#json_log").write(" ")

                if ipc_message.type == "TRANSCRIPTION":
                    self.chat_log_content = "" + "[bold red]You:\n[white]" + ipc_message.data.upper() + "\n"
                    self.query_one("#chat_log").update(self.chat_log_content)

                if ipc_message.type == "RAW_TRANSCRIPTION":
                    message_box = self.query_one("#transcription_message")
                    message_box.update(ipc_message.data)

                if ipc_message.type == "RECORD_STATUS":
                    message = ipc_message.data

                    if message == "ready":
                        self.listen_status.styles.color = "green"

                if ipc_message.type == "LISTEN_STATUS":
                    message = ipc_message.data

                    if message == "ready":
                        self.listen_status.styles.color = "greenyellow"

                    if message == "not_ready":
                        self.listen_status.styles.color = "red"

                    if message == "listening":
                        self.listen_status.styles.color = "blue"

                if ipc_message.type == "TRANSCRIBER_STATUS":
                    message = ipc_message.data

                    if message == "ready":
                        self.transcriber_status.styles.color = "greenyellow"

                    if message == "not_ready":
                        self.transcriber_status.styles.color = "red"

                    if message == "transcribing":
                        self.transcriber_status.styles.color = "blue"

                if ipc_message.type == "AGENT_STATUS":
                    message = ipc_message.data

                    if message == "ready":
                        self.agent_status.styles.color = "greenyellow"

                    if message == "thinking":
                        self.agent_status.styles.color = "blue"

                    if message == "speaking":
                        self.agent_status.styles.color = "orange"


            await asyncio.sleep(0.1)



