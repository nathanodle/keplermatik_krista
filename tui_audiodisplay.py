import numpy as np
from PIL import Image
import copy
from textual.widgets import Static
from textual.widget import Widget
from rich.text import Text
from textual import events

class TUIAudioDisplay(Static):
    def __init__(self,
                 name: str | None = None,
                 id: str | None = None,
                 classes: str | None = None, ):

        super().__init__(name=name, id=id, classes=classes)


    # def on_mount(self) -> None:
    #     print("MOUNT " + str(self._size.width) + str(self._size.height))
    #     self.create_text_image(self._size.width, self._size.height)
    #     self.map_buffer = copy.deepcopy(self.base_image)
    #     self.update_map(0, 0)

    def on_resize(self, event: events.Resize) -> None:
        size = event.virtual_size
        print(size)

        self.update_map(0, 0)



    def update_map(self, lat, lon) -> None:
        #print("updating map")
        test = Text()

        line_buffer = Text.from_ansi("test", no_wrap=True, justify="Left")

        self.update(line_buffer)

