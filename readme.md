
<a href="https://github.com/mysteriousham73/PyKeplermatik`/">
    <img src="https://i.imgur.com/Od9Y0V6.png" alt="Keplermatik logo" title="Keplermatik    " "left" height="60" />
</a>

# Keplermatik

### Keplermatik is a suite of interconnected tools to predict satellite orbits.
**This is a hobbyist-scale project, currently being refined for public use.  Installation, CI, and other documentation is in the works!**

## Table of contents

- [Architecture](#installation)
    - [PyKeplermatik](#PyKepermatik)
    - [Keplermatik Krista](#Keplermatik-Krista)
    - [Keplermatik TUI](#Keplermatik-TUI)

- [License](#license)
- [Links](#links)

## Architecture

### PyKepermatik
The central core of the system is a fast, open-source websockets server that provides satellite predictions to connected clients.  It uses Python multiprocessing to make predictions in an efficient manner, using Brandon Rhodes's brilliant [Skyfield](https://github.com/skyfielders/python-skyfield) library and its NumPy implementation of the Simplified General Perturbations propagator, which is among the best out there.  It also provides management of Two Line Elements (TLEs), ensuring that the most recent are available using a combination of those available from [SatNOGS](https://satnogs.org/) and [Celestrak](https://celestrak.org/).  It provides satellite uplink/downlink information from Satnogs and can calculate the doppler shift of a signal at the observer's location. 

[PyKeplermatik](https://github.com/mysteriousham73/PyKeplermatik) currently handles predictions of a satellite's current location, as well as observer-dependent information such as azimuth and elevation.  In the works: future pass prediction, satellite horizon/footprint, and other useful features. 

### Keplermatik Krista

[Keplermatik Krista](https://github.com/mysteriousham73/keplermatik_krista) is a voice assistant that can provide any information from PyKeplermatik in an easily accessible format.

This assistant is named after [Crista McAullife](https://en.wikipedia.org/wiki/Christa_McAuliffe), the teacher lost in the Space Shuttle Challenger disaster in 1986.  As a schoolteacher she impacted many lives and inspired children around the world. 

Krista builds on the following technologies:

- [Amazon Polly](https://aws.amazon.com/polly/)  While there are many open-source text-to-speech models currently in development, they're not yet responsive enough on consumer hardware to use with a voice assistant.  Krista therefore utilizes Amazon Polly's Neural Salli voice to provide a response.
  

- [OpenAI Whisper](https://github.com/openai/whisper) for locally hosted speech-to-text.  Using the medium model and a healthy GPU, it is responsive and provides enough accuracy for working with difficult to transcribe satellite names like "AO-7"
  

- [OpenAI GPT-3](https://beta.openai.com/docs/models/gpt-3) for transforming user requests into a JSON representation of the request, using the following format: 
```
  {
      "question": "what is the next time that AO-7 will be visible from my location?",
      "category": "satellite_pass_prediction",
      "input_parameters": {
            "satellite": "AO-7",
            "location": "my_location",
            "pass_numbers": [0]
      },
      "output_parameters": [
        "satellite_rise_time",
        "satellite_set_time",
        "satellite_maximum_elevation"
      ]
  }
  ```

  This works remarkably well, better than it should but such is the power of Large Language Models (LLMs).  It works by utilizing a conditioning prompt that provides a list of satellites and a set of JSON responses, combined with the following instruction:

**gpt_prompt = satlist + "is a list of valid satellites." + sample_responses + " is a list of sample responses. make sure satellite is in the list of valid satellites, and set satellite to 'unknown' if it is not.  form the following question into properly formatted json as above:"+ string + "{\n \"question\":"**

This JSON is then processed by the system which will link in information from the PyKeplermatik server to build a response to the user.

That response is then fed back into GPT-3 to format it into conversational language and spoken to the user through Polly. 

### Keplermatik TUI

Not yet but soon to be public on GitHub is a TUI (Text User Interface) which provides graphical representation of the satellite's location over the earth's surface.  As PyKeplermatik progresses, it will also be able to plot future orbits as well as sun/shadow.  Additionally, it will display an easy to navigate interface for choosing satellites and up/downlinks.

Maps are generated on-the-fly from a high-resolution raster image, ensuring that they look great on large terminals.  The [Textualize](https://github.com/Textualize/textual) library makes for a modern, responsive UI.

Also planned (for fun!) is a dial-up server which will host Keplermatik TUI for those with retrocomputing interests :)

<a href="https://github.com/mysteriousham73/PyKeplermatik`/">
<img src="https://i.imgur.com/MoWhES2.jpg" alt="Keplermatik TUI" title="Keplermatik  TUI  " "left" height="100" />
</a>

## License

For now, PyKeplermatik is using the [SSPL](https://en.wikipedia.org/wiki/Server_Side_Public_License).  Some might not consider it true open source, but it's a 'safe' option until less restrictive alternatives are considered.  In the meantime, feel free to contact for other licensing requests, we're pretty open-minded!  

## Links

To read about an ongoing, decade-long project that's the spiritual predecessor to PyKeplermatik, check out the original [Keplermatik on Hackaday.io](https://hackaday.io/project/5358-keplermatik)

This project uses only Cold War-era tech such as Transputers(!) to essentially do the same job as PyKeplermatik.  Not a lot of updates the past couple years, it's hard :)

