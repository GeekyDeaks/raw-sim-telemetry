from bokeh.plotting import figure, output_file, show
from bokeh.events import MouseMove
from bokeh.layouts import column, row
from bokeh.models import Div, ColumnDataSource, RangeTool, LinearAxis, Range1d, Title, FileInput, CustomJS, HoverTool, Span
import csv
from datetime import datetime
import argparse
import numpy
import math

def distance(a, b):
    return math.sqrt( (a[0] - b[0]) **2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def load_lap(file, ilen=0):

    data = {}
    i = {}
    last_point = None
    dt = 0
    with open(file,'r') as dest_f:
        reader = csv.reader(dest_f, delimiter='\t')

        dist = []
        headers = next(reader, None)
        for h in headers:
            data[h] = []

        for row in reader:

            for h, v in zip(headers, row):
                data[h].append(float(v))

            cur_point = (data['x'][-1], data['y'][-1], data['z'][-1])
            if last_point:
                # calc the delta
                dt = dt + distance(last_point, cur_point)

            dist.append(dt)
            last_point = cur_point

        total_dist = math.ceil(dist[-1])  

        # how many interpolation points?  
        if ilen == 0:
            ilen =  total_dist
        
        i['distance'] = list(range(ilen))

        # what is the ratio to the total distance of each point?
        iratio = total_dist / ilen

        ird = list(map(lambda x: x * iratio, i['distance']))

        for d in data:
            i[d] = numpy.interp(ird, dist, data[d]).tolist()

    return i

def invert_data(data):
    return list(map( lambda x: -x, data))


def combined_charts(file1, file2, output='plot.html', plot_width=1000, plot_height=600):

    data1 = load_lap(file1)
    ilen = len(data1['distance'])

    data2 = load_lap(file2, ilen=ilen)

    delta = []
    for i,j in zip(data1['lapTime'],data2['lapTime']):
        delta.append(float(j) - float(i))

    data = {
        'distance': data1['distance'],
        'mph1': data1['speed_Mph'],
        'mph2': data2['speed_Mph'],
        'gas1': data1['gas'],
        'gas2': data2['gas'],
        'brake1': data1['brake'],
        'brake2': data2['brake'],
        'delta': delta,
        'x1': data1['x'],
        'z1': invert_data(data1['z']),
        'x2': data2['x'],
        'z2': invert_data(data2['z'])
    }

    # calculate a starting range
    range_start=int(ilen * 0.25)
    range_end=int(ilen * 0.5)
    range_mid = int( (range_end - range_start) / 2 + range_start  )

    # some initial data for the track, using the range determined above
    track_source = ColumnDataSource(data=dict(
        x1=data['x1'][range_start:range_end], 
        z1=data['z1'][range_start:range_end], 
        x2=data['x2'][range_start:range_end],
        z2=data['z2'][range_start:range_end]
    ))

    pos_source = ColumnDataSource(data=dict(
        x1=[ data['x1'][range_mid] ],
        z1=[ data['z1'][range_mid] ],
        x2=[ data['x2'][range_mid] ],
        z2=[ data['z2'][range_mid] ],
    ))

    source = ColumnDataSource(data=data)

    # output to static HTML file
    output_file(output, title='AC Telemetry')

    # main plot showing the telemetry
    p = figure(
        plot_height=plot_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan', x_axis_label='distance', y_axis_label='mph',
            x_range=(range_start, range_end))

    lap1time = datetime.fromtimestamp(data1['lapTime'][-1]).strftime('%M:%S:%f')[:-3]
    lap2time = datetime.fromtimestamp(data2['lapTime'][-1]).strftime('%M:%S:%f')[:-3]

    p.add_layout(Title(text="(2) " + lap2time + ' | ' + file2, text_font_style="normal"), 'above')
    p.add_layout(Title(text="(1) " + lap1time + ' | ' + file1, text_font_style="bold"), 'above')
    p.add_layout(Title(text="AC Telemetry", text_font_size="16pt"), 'above')

    hover_tool = HoverTool(
        tooltips = [
            ('mph', '@mph1{0.00 a} / @mph2{0.00 a}'),
            ('gas', '@gas1{0.00 a} / @gas2{0.00 a}'),
            ('brake', '@brake1{0.00 a} / @brake2{0.00 a}'),
            ('delta', '@delta{0.00 a}')
        ],
        mode = 'vline',
        names=['mph2']
    )
    p.add_tools(hover_tool)

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
    track.line('x1', 'z1', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap1', color='green')
    track.line('x2', 'z2', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap2', color='blue', line_dash='dashed')
    track.circle_cross('x1', 'z1', source=pos_source, size=20, color='green', alpha=0.2)
    track.circle_cross('x2', 'z2', source=pos_source, size=20, color='blue', alpha=0.2)
    track.legend.location = "top_left"
    track.legend.click_policy="mute"
    # make sure the units are kept the same on x,z
    track.match_aspect = True

    # create a new range for the pedals and assign the scale to the right
    p.extra_y_ranges['pedal'] = Range1d(start=0, end=1.01)
    p.add_layout(LinearAxis(y_range_name='pedal', axis_label='pedal'), 'right')

    # add all the telemetry lines
    p.line('distance', 'mph1', name='mph1', muted_alpha=0.2, source=source, legend_label="mph1", line_width=2)
    p.line('distance', 'mph2', name='mph2', muted_alpha=0.2, source=source, legend_label="mph2", line_width=2, line_dash='dashed')
    p.line('distance', 'gas1', name='gas1', muted_alpha=0.2, source=source, color='green', legend_label="gas1", line_width=2, y_range_name = 'pedal')
    p.line('distance', 'gas2', name='gas2', muted_alpha=0.2, source=source, color='green', legend_label="gas2", line_width=2, line_dash='dashed', y_range_name = 'pedal')
    p.line('distance', 'brake1', name='brake1', muted_alpha=0.2, source=source, color='red', legend_label="brake1", line_width=2, y_range_name = 'pedal')
    p.line('distance', 'brake2', name='brake2', muted_alpha=0.2, source=source, color='red', legend_label="brake2", line_width=2, line_dash='dashed', y_range_name = 'pedal')

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

    mid_span = Span(location=range_mid, dimension='height', line_dash='solid', 
        line_color='black', line_width=3, line_alpha=0.2)
    p.add_layout(mid_span)
    select.add_layout(mid_span)

    hover_update = CustomJS(args=dict(src=source, pos_source=pos_source, mid_span=mid_span), code= """
        var s = src.data
        var p = pos_source.data
        var mid = Math.floor(cb_obj.x)

        mid_span.location = mid

        p['x1'][0] = s['x1'][mid]
        p['z1'][0] = s['z1'][mid]
        p['x2'][0] = s['x2'][mid]
        p['z2'][0] = s['z2'][mid]

        pos_source.change.emit()
    """)

    p.js_on_event(MouseMove, hover_update)
    # when the range changes, update the track points we are plotting
    trk_update = CustomJS(args=dict(src=source, dst=track_source, mid_span=mid_span, pos_source=pos_source), code= """
        var s = src.data
        var d = dst.data
        var p = pos_source.data
        const start = Math.max(0, cb_obj.start)
        const end = Math.min(s['x1'].length, cb_obj.end)
        const mid = Math.round( (cb_obj.end - cb_obj.start) / 2 + cb_obj.start )

        mid_span.location = mid

        p['x1'][0] = s['x1'][mid]
        p['z1'][0] = s['z1'][mid]
        p['x2'][0] = s['x2'][mid]
        p['z2'][0] = s['z2'][mid]

        d['x1'] = s['x1'].slice(start, end)
        d['z1'] = s['z1'].slice(start, end)
        d['x2'] = s['x2'].slice(start, end)
        d['z2'] = s['z2'].slice(start, end)
        dst.change.emit()
        pos_source.change.emit()
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


def split_charts(file1, file2, output='plot.html', plot_width=1000, plot_height=600):

    data1 = load_lap(file1)
    ilen = len(data1['distance'])

    data2 = load_lap(file2, ilen=ilen)

    delta = []
    for i,j in zip(data1['lapTime'],data2['lapTime']):
        delta.append(float(j) - float(i))

    data = {
        'distance': data1['distance'],
        'mph1': data1['speed_Mph'],
        'mph2': data2['speed_Mph'],
        'gas1': data1['gas'],
        'gas2': data2['gas'],
        'brake1': data1['brake'],
        'brake2': data2['brake'],
        'steer1': data1['steer'],
        'steer2': data2['steer'],
        'delta': delta,
        'x1': data1['x'],
        'z1': invert_data(data1['z']),
        'x2': data2['x'],
        'z2': invert_data(data2['z'])
    }

    # calculate a starting range
    range_start=int(ilen * 0.25)
    range_end=int(ilen * 0.5)
    range_mid = int( (range_end - range_start) / 2 + range_start  )

    # some initial data for the track, using the range determined above
    track_source = ColumnDataSource(data=dict(
        x1=data['x1'][range_start:range_end], 
        z1=data['z1'][range_start:range_end], 
        x2=data['x2'][range_start:range_end],
        z2=data['z2'][range_start:range_end]
    ))

    pos_source = ColumnDataSource(data=dict(
        x1=[ data['x1'][range_mid] ],
        z1=[ data['z1'][range_mid] ],
        x2=[ data['x2'][range_mid] ],
        z2=[ data['z2'][range_mid] ],
    ))

    source = ColumnDataSource(data=data)

    # output to static HTML file
    output_file(output, title='AC Telemetry')

    trace_height = int(plot_height/4)

    # main plot showing the telemetry
    fig_mph = figure(
        plot_height=trace_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan', x_axis_label='distance', y_axis_label='mph',
            x_range=(range_start, range_end))

    lap1time = datetime.fromtimestamp(data1['lapTime'][-1]).strftime('%M:%S:%f')[:-3]
    lap2time = datetime.fromtimestamp(data2['lapTime'][-1]).strftime('%M:%S:%f')[:-3]


    # add all the telemetry lines
    fig_mph.line('distance', 'mph1', name='mph1', muted_alpha=0.2, source=source, legend_label="lap1", line_width=2)
    fig_mph.line('distance', 'mph2', name='mph2', muted_alpha=0.2, source=source, legend_label="lap2", line_width=2, line_dash='dashed')
    fig_mph.legend.location = "top_left"
    fig_mph.legend.click_policy="mute"

    mph_hover_tool = HoverTool(
        tooltips = [('mph1', '@mph1{0.00 a}'), ('mph2', '@mph2{0.00 a}'),('delta', '@delta{0.00 a}')],
        mode = 'vline',
        names=['mph1']
    )
    fig_mph.add_tools(mph_hover_tool)

    # main plot showing the telemetry
    fig_gas = figure(
        plot_height=trace_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan', x_axis_label='distance', y_axis_label='gas',
            x_range=fig_mph.x_range)
    fig_gas.line('distance', 'gas1', name='gas1', muted_alpha=0.2, source=source, color='green', legend_label="lap1", line_width=2)
    fig_gas.line('distance', 'gas2', name='gas2', muted_alpha=0.2, source=source, color='green', legend_label="lap2", line_width=2, line_dash='dashed')
    fig_gas.legend.location = "top_left"
    fig_gas.legend.click_policy="mute"

    gas_hover_tool = HoverTool(
        tooltips = [('gas1', '@gas1{0.00 a}'), ('gas2', '@gas2{0.00 a}'),('delta', '@delta{0.00 a}')],
        mode = 'vline',
        names=['gas1']
    )
    fig_gas.add_tools(gas_hover_tool)

    # main plot showing the telemetry
    fig_brake = figure(
        plot_height=trace_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan', x_axis_label='distance', y_axis_label='brake',
            x_range=fig_mph.x_range)
    fig_brake.line('distance', 'brake1', name='brake1', muted_alpha=0.2, source=source, color='red', legend_label="lap1", line_width=2)
    fig_brake.line('distance', 'brake2', name='brake2', muted_alpha=0.2, source=source, color='red', legend_label="lap2", line_width=2, line_dash='dashed')
    fig_brake.legend.location = "top_left"
    fig_brake.legend.click_policy="mute"

    brake_hover_tool = HoverTool(
        tooltips = [('brake1', '@brake1{0.00 a}'), ('brake2', '@brake2{0.00 a}'),('delta', '@delta{0.00 a}')],
        mode = 'vline',
        names=['brake1']
    )
    fig_brake.add_tools(brake_hover_tool)

    # main plot showing the telemetry
    fig_steer = figure(
        plot_height=trace_height, plot_width=int(plot_width * .6),
        toolbar_location=None,
        tools='xpan', x_axis_label='distance', y_axis_label='steer',
            x_range=fig_mph.x_range)
    fig_steer.line('distance', 'steer1', name='steer1', muted_alpha=0.2, source=source, color='orange', legend_label="lap1", line_width=2)
    fig_steer.line('distance', 'steer2', name='steer2', muted_alpha=0.2, source=source, color='orange', legend_label="lap2", line_width=2, line_dash='dashed')
    fig_steer.legend.location = "top_left"
    fig_steer.legend.click_policy="mute"
    fig_steer.y_range.flipped = True

    steer_hover_tool = HoverTool(
        tooltips = [('steer1', '@steer1{0.00 a}'), ('steer2', '@steer2{0.00 a}'),('delta', '@delta{0.00 a}')],
        mode = 'vline',
        names=['steer1']
    )
    fig_steer.add_tools(steer_hover_tool)

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
    track.line('x1', 'z1', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap1', color='green')
    track.line('x2', 'z2', source=track_source, line_width=2, muted_alpha=0.2, legend_label='lap2', color='blue', line_dash='dashed')
    track.circle_cross('x1', 'z1', source=pos_source, size=20, color='green', alpha=0.2)
    track.circle_cross('x2', 'z2', source=pos_source, size=20, color='blue', alpha=0.2)
    track.legend.location = "top_left"
    track.legend.click_policy="mute"
    # make sure the units are kept the same on x,z
    track.match_aspect = True

    # this is the little block that shows the current range
    range_tool = RangeTool(x_range=fig_mph.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = .2

    # the range selection uses a plot of the delta
    select.line('distance', 'delta', source=source)
    select.add_tools(range_tool)
    select.toolbar.active_multi = range_tool

    mid_span = Span(location=range_mid, dimension='height', line_dash='solid', 
        line_color='black', line_width=3, line_alpha=0.2)
    fig_mph.add_layout(mid_span)
    fig_gas.add_layout(mid_span)
    fig_brake.add_layout(mid_span)
    fig_steer.add_layout(mid_span)
    select.add_layout(mid_span)

    hover_update = CustomJS(args=dict(src=source, pos_source=pos_source, mid_span=mid_span), code= """
        var s = src.data
        var p = pos_source.data
        var mid = Math.floor(cb_obj.x)

        mid_span.location = mid

        p['x1'][0] = s['x1'][mid]
        p['z1'][0] = s['z1'][mid]
        p['x2'][0] = s['x2'][mid]
        p['z2'][0] = s['z2'][mid]

        pos_source.change.emit()
    """)

    fig_mph.js_on_event(MouseMove, hover_update)
    fig_gas.js_on_event(MouseMove, hover_update)
    fig_brake.js_on_event(MouseMove, hover_update)
    fig_steer.js_on_event(MouseMove, hover_update)

    # when the range changes, update the track points we are plotting
    trk_update = CustomJS(args=dict(src=source, dst=track_source, mid_span=mid_span, pos_source=pos_source), code= """
        var s = src.data
        var d = dst.data
        var p = pos_source.data
        const start = Math.max(0, cb_obj.start)
        const end = Math.min(s['x1'].length, cb_obj.end)
        const mid = Math.round( (cb_obj.end - cb_obj.start) / 2 + cb_obj.start )

        mid_span.location = mid

        p['x1'][0] = s['x1'][mid]
        p['z1'][0] = s['z1'][mid]
        p['x2'][0] = s['x2'][mid]
        p['z2'][0] = s['z2'][mid]

        d['x1'] = s['x1'].slice(start, end)
        d['z1'] = s['z1'].slice(start, end)
        d['x2'] = s['x2'].slice(start, end)
        d['z2'] = s['z2'].slice(start, end)
        dst.change.emit()
        pos_source.change.emit()
    """)

    fig_mph.x_range.js_on_change('start', trk_update) 
    fig_mph.x_range.js_on_change('end', trk_update) 

    # allow dynamic sizing
    fig_mph.sizing_mode = 'stretch_width'
    fig_gas.sizing_mode = 'stretch_width'
    fig_brake.sizing_mode = 'stretch_width'
    fig_steer.sizing_mode = 'stretch_width'
    #p.width_policy = 'max'
    #track.sizing_mode = 'stretch_width'
    #track.width_policy = 'min'
    select.sizing_mode = 'stretch_width'
    # display the charts
    trace_col = column(fig_mph, fig_gas, fig_brake, fig_steer)
    trace_col.sizing_mode = 'stretch_width'
    row1 = row(trace_col, track)
    row1.sizing_mode = 'stretch_width'
    subtitle =  column(
        Div(text='<strong>(1) ' + lap1time + '</strong> | ' + file1),
        Div(text="<strong>(2) " + lap2time + '</strong> | ' + file2)
    )
    subtitle.sizing_mode = 'stretch_width'
    title = row( 
        Div(text='<h1 style="margin:0;">Sim Telemetry</h1>'),
        subtitle
    )
    title.sizing_mode = 'stretch_width'
    col = column(title, row1, select)
    col.sizing_mode = 'stretch_width'
    show(col)


if __name__ == '__main__':


    parser = argparse.ArgumentParser(description='Raw Telemetry Plotter')
    parser.add_argument('lap1', nargs='?', help='reference lap file')
    parser.add_argument('lap2', nargs='?', help='compare lap file')  
    parser.add_argument('out', nargs='?', default='plot.html', help='output filename')

    args = parser.parse_args()

    print(args.out)

    split_charts(args.lap1, args.lap2, output=args.out)