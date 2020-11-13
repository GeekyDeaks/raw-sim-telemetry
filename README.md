# AC Telemetry

Crude Assetto Corsa Telemetry logger, written specifically to address the lack of tools for the PS4/XB1

# get started

    python3 logger.py [IP address]

This will intiate the telemetry feed from an instance of AC running on the target IP.
It will log telemetry per lap into a subdirectory of the `log` directory, 
with one row per approximate meter travelled and a summary `laps.txt`

# plotting

To plot you will need to install the [bokeh](https://docs.bokeh.org/en/latest/index.html) module. I recommend creating a `venv` e.g.

    python3 -m venv py
    py/bin/pip install bokeh
    py/bin/python plot.py [lap1 file] [lap2 file]

This will create an output html file that looks something like this:

![example](example.png)

You can click on the legends to mute any trace and the bottom slider allows you to narrow down the analysis
to a specific range of measurements

# TODO

* log all the updates from AC rather than per approximate meter
* interpolate updates in the plot

# reference

* https://docs.google.com/document/d/1KfkZiIluXZ6mMhLWfDX1qAGbvhGRC3ZUzjVIt5FQpp4/pub
* https://docs.bokeh.org/en/latest/index.html