from bokeh.plotting import figure, output_file, show

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, RangeTool, LinearAxis, Range1d, Title, FileInput, CustomJS
import csv
import argparse

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

def pad_data(data, padlen):
    return data + ([float('NaN')] * (padlen - len(data)) )

def invert_data(data):
    return list(map( lambda x: -x, data))


def combined_charts(file1, file2, output='plot.html', plot_width=1000, plot_height=600):

    data1 = load_lap(file1)
    data2 = load_lap(file2)

    dlen1 = len(data1['distance'])
    dlen2 = len(data2['distance'])

    # prepare some padded data
    padto = max(dlen1, dlen2)

    delta = []
    for i,j in zip(data1['lapTime'],data2['lapTime']):
        delta.append(float(j) - float(i))

    data = {
        'mph1': pad_data(data1['speed_Mph'], padto),
        'mph2': pad_data(data2['speed_Mph'], padto),
        'gas1': pad_data(data1['gas'], padto),
        'gas2': pad_data(data2['gas'], padto),
        'brake1': pad_data(data1['brake'], padto),
        'brake2': pad_data(data2['brake'], padto),
        'delta': pad_data(delta, padto),
        'x1': pad_data(invert_data(data1['x']), padto),
        'z1': pad_data(data1['z'], padto),
        'x2': pad_data(invert_data(data2['x']), padto),
        'z2': pad_data(data2['z'], padto)
    }

    # calculate a starting range
    range_start=int(padto * 0.25)
    range_end=int(padto * 0.5)

    # some initial data for the track, using the range determined above
    track_source = ColumnDataSource(data=dict(
        x1=data['x1'][range_start:range_end], 
        z1=data['z1'][range_start:range_end], 
        x2=data['x2'][range_start:range_end],
        z2=data['z2'][range_start:range_end]
    ))

    # we want to use the distance of the longest list
    if dlen1 < dlen2:
        data['distance'] = data2['distance']
    else:
        data['distance'] = data1['distance']

    source = ColumnDataSource(data=data)

    # output to static HTML file
    output_file(output)

    TOOLTIPS = [
        ("distance", "$x"),
        ("value", "$y")
    ]

    # main plot showing the telemetry
    p = figure(
        plot_height=plot_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan, hover',
        tooltips=TOOLTIPS, x_axis_label='distance', y_axis_label='mph',
            x_range=(range_start, range_end))

    p.add_layout(Title(text="(2) " + file2, text_font_style="italic"), 'above')
    p.add_layout(Title(text="(1) " + file1, text_font_style="italic"), 'above')
    p.add_layout(Title(text="AC Telemetry", text_font_size="16pt"), 'above')

    # zoom plot used to narrow down the other plots
    # shows the delta from lap1 to lap2
    select = figure(title="Drag the middle and edges of the selection box to change the range above",
                    plot_height=130, plot_width=plot_width,
                    x_axis_type=None, y_axis_label='delta (s)',
                    tools="", toolbar_location=None, background_fill_color="#f9f9f9")

    # track plot
    # uses a dynamically created set of data, essentially the list of x,z that 
    # would be visible with the range currently set
    track = figure(title='Track', plot_width=int(plot_width * .4), plot_height=plot_height, 
        tools='', toolbar_location=None, x_axis_label='meters', y_axis_label='meters')
    track.line('x1', 'z1', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap1')
    track.line('x2', 'z2', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap2', line_dash='dashed')
    track.legend.location = "top_left"
    track.legend.click_policy="mute"
    # make sure the units are kept the same on x,z
    track.match_aspect = True

    # create a new range for the pedals and assign the scale to the right
    p.extra_y_ranges['pedal'] = Range1d(start=0, end=1.01)
    p.add_layout(LinearAxis(y_range_name='pedal', axis_label='pedal'), 'right')

    # add all the telemetry lines
    p.line('distance', 'mph1', muted_alpha=0.2, source=source, legend_label="mph1", line_width=2)
    p.line('distance', 'mph2', muted_alpha=0.2, source=source, legend_label="mph2", line_width=2, line_dash='dashed')
    p.line('distance', 'gas1', muted_alpha=0.2, source=source, color='green', legend_label="gas1", line_width=2, y_range_name = 'pedal')
    p.line('distance', 'gas2', muted_alpha=0.2, source=source, color='green', legend_label="gas2", line_width=2, line_dash='dashed', y_range_name = 'pedal')
    p.line('distance', 'brake1', muted_alpha=0.2, source=source, color='red', legend_label="brake1", line_width=2, y_range_name = 'pedal')
    p.line('distance', 'brake2', muted_alpha=0.2, source=source, color='red', legend_label="brake2", line_width=2, line_dash='dashed', y_range_name = 'pedal')

    p.legend.location = "top_left"
    p.legend.click_policy="mute"

    # this is the little block that shows the current range
    range_tool = RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = .2

    # the range selection uses a plot of the delta
    select.line('distance', 'delta', source=source)
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    # when the range changes, update the track points we are plotting
    trk_update = CustomJS(args=dict(src=source, dst=track_source), code= """
        var s = src.data;
        var d = dst.data;
        const start = Math.max(0, cb_obj.start)
        const end = Math.min(s['x1'].length, cb_obj.end)

        d['x1'] = s['x1'].slice(start, end)
        d['z1'] = s['z1'].slice(start, end)
        d['x2'] = s['x2'].slice(start, end)
        d['z2'] = s['z2'].slice(start, end)
        dst.change.emit();
    """)

    p.x_range.js_on_change('start', trk_update) 
    p.x_range.js_on_change('end', trk_update) 

    # allow dynamic sizing
    p.sizing_mode = 'stretch_width'
    #p.width_policy = 'max'
    #track.sizing_mode = 'stretch_width'
    #track.width_policy = 'min'
    select.sizing_mode = 'stretch_width'
    # display the charts
    row1 = row(p, track)
    row1.sizing_mode = 'stretch_width'
    col = column(row1, select)
    col.sizing_mode = 'stretch_width'
    show(col)


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Assetto Corsa Telemetry Plotter')
    parser.add_argument('lap1', nargs='?', help='reference lap file')
    parser.add_argument('lap2', nargs='?', help='compare lap file')  
    parser.add_argument('out', nargs='?', help='output filename')

    args = parser.parse_args()

    combined_charts(args.lap1, args.lap2, output=args.out)