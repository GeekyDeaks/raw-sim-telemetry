from bokeh.plotting import figure, output_file, show

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, RangeTool, LinearAxis, Range1d
import math

import csv

file1 = 'log/imola/ks_corvette_c7r/20201112T183406.636080_Scott_Deakin/lap_0.txt'
file2 = 'log/imola/ks_corvette_c7r/20201112T181836.263851_Scott_Deakin/lap_0.txt'

plot_width=1200
plot_height=600

def load_lap(file):

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
                data[h].append(float(v))
    return data

data1 = load_lap(file1)
data2 = load_lap(file2)


# prepare some data
dlen = min(len(data1['gas']), len(data2['gas']))
print(dlen)
delta = []
for i,j in zip(data1['lapTime'],data2['lapTime']):
    delta.append(int(j) - int(i))

data = {
    'distance': data1['distance'][:dlen],
    'mph1': data1['speed_Mph'][:dlen],
    'mph2': data2['speed_Mph'][:dlen],
    'gas1': data1['gas'][:dlen],
    'gas2': data2['gas'][:dlen],
    'brake1': data1['brake'][:dlen],
    'brake2': data2['brake'][:dlen],
    'delta': delta
}

source = ColumnDataSource(data=data)

# output to static HTML file
output_file("lines.html")

# create a new plot with a title and axis labels
p = figure(
    plot_height=plot_height, plot_width=plot_width,
    toolbar_location=None,
    tools='xpan, hover',
    title="AC Telemetry", x_axis_label='distance', y_axis_label='mph',
        x_range=(200, 800))


select = figure(title="Drag the middle and edges of the selection box to change the range above",
                plot_height=130, plot_width=plot_width,
                x_axis_type=None, y_axis_label='delta (s)',
                tools="", toolbar_location=None, background_fill_color="#efefef")


mph1_max = max(data['mph1'])
mph2_max = max(data['mph2'])
p.y_range = Range1d(start=0, end=max(mph1_max, mph2_max) )
p.extra_y_ranges['pedal'] = Range1d(start=0, end=1.01)
p.add_layout(LinearAxis(y_range_name='pedal', axis_label='pedal'), 'right')

# add a line renderer with legend and line thickness
p.line('distance', 'mph1', source=source, line_width=2)
p.line('distance', 'mph2', source=source, line_width=2, line_dash='dashed')
p.line('distance', 'gas1', source=source, color='green', legend_label="gas", line_width=2, y_range_name = 'pedal')
p.line('distance', 'gas2', source=source, color='green', line_width=2, line_dash='dashed', y_range_name = 'pedal')
p.line('distance', 'brake1', source=source, color='red', legend_label="brake", line_width=2, y_range_name = 'pedal')
p.line('distance', 'brake2', source=source, color='red', line_width=2, line_dash='dashed', y_range_name = 'pedal')


range_tool = RangeTool(x_range=p.x_range)
range_tool.overlay.fill_color = "navy"
range_tool.overlay.fill_alpha = 0.2

select.y_range = Range1d(start=min(data['delta']), end=max(data['delta']) )
select.line('distance', 'delta', source=source)
select.ygrid.grid_line_color = None
select.add_tools(range_tool)
select.toolbar.active_multi = range_tool

# show the results
show(column(p, select))