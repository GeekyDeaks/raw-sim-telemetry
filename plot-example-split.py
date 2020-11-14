
import plot

file1 = 'log/imola/ks_corvette_c7r/20201112T215006_Scott_Deakin/lap_2.txt'
file2 = 'log/imola/ks_corvette_c7r/20201112T215006_Scott_Deakin/lap_0.txt'

plot_width=1000
plot_height=600

plot.split_charts(file1, file2, output='example-split.html', plot_width=plot_width, plot_height=plot_height)