from bokeh.plotting import figure, output_file, show

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool, LinearAxis, Range1d

import csv

file = 'out/20201110T143416.593749_7_Scott_Deakin_pm3dm_nissan_primera_btcc_croft_croft.txt'

data = {}
with open(file,'r') as dest_f:
    reader = csv.reader(dest_f, delimiter='\t')

    data['distance'] = []
    headers = next(reader, None)
    for h in headers:
        data[h] = []

    for row in reader:
        data['distance'].append(reader.line_num - 1)
        for h, v in zip(headers, row):
            data[h].append(v)


#print(data)


# prepare some data

source = ColumnDataSource(data=data)

# output to static HTML file
output_file("lines.html")

# create a new plot with a title and axis labels
p = figure(
    plot_height=400, plot_width=1000,
    toolbar_location=None,
    tools='xpan, hover',
    title="simple line example", x_axis_label='distance', y_axis_label='y',
        x_range=(200, 800))


select = figure(title="Drag the middle and edges of the selection box to change the range above",
                plot_height=130, plot_width=1000, y_range=p.y_range,
                x_axis_type=None, y_axis_type=None,
                tools="", toolbar_location=None, background_fill_color="#efefef")

p.y_range = Range1d(0, 1)
p.extra_y_ranges['mph'] = Range1d(start=0, end=200)
p.add_layout(LinearAxis(y_range_name='mph', axis_label='mph'), 'right')

# add a line renderer with legend and line thickness
p.line('distance', 'speed_Mph', source=source, legend_label="mph", line_width=2, y_range_name = 'mph')
p.line('distance', 'gas', source=source, color='green', legend_label="gas", line_width=2)
p.line('distance', 'brake', source=source, color='red', legend_label="gas", line_width=2)





range_tool = RangeTool(x_range=p.x_range)
range_tool.overlay.fill_color = "navy"
range_tool.overlay.fill_alpha = 0.2

select.line('distance', 'gas', source=source, color='green')
select.line('distance', 'brake', source=source, color='red')
select.ygrid.grid_line_color = None
select.add_tools(range_tool)
select.toolbar.active_multi = range_tool

# show the results
show(column(p, select))