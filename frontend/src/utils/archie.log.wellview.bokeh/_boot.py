from bokeh.layouts import gridplot

from bokeh.models import Range1d
from bokeh.models import LinearAxis

from bokeh.plotting import figure

def boot(layout):

	heads,bodys = [],[]

	for index in range(layout.trail):

		head = figure(width=layout.width[index],height=layout.height[0])
		body = figure(width=layout.width[index],height=layout.height[1])

		head.add_layout(LinearAxis(major_label_text_alpha=0),'right')
		head.add_layout(LinearAxis(major_label_text_alpha=0),'above')

		body.add_layout(LinearAxis(major_label_text_alpha=0),'right')
		body.add_layout(LinearAxis(major_label_text_alpha=0),'above')

		head.y_range = Range1d(*layout.label.limit)
		body.y_range = Range1d(*layout.depth.limit)

		head.x_range = Range1d(*layout[index].limit)
		body.x_range = Range1d(*layout[index].limit)

		head.xaxis.major_label_text_font_size = '0pt'
		head.yaxis.major_label_text_font_size = '0pt'

		body.xaxis.major_label_text_font_size = '0pt'
		body.yaxis.major_label_text_font_size = '0pt'

		head.xaxis.major_tick_in = 0
		head.yaxis.major_tick_in = 0
		body.xaxis.major_tick_in = 0
		body.yaxis.major_tick_in = 0

		head.xaxis.major_tick_out = 0
		head.yaxis.major_tick_out = 0
		body.xaxis.major_tick_out = 0
		body.yaxis.major_tick_out = 0

		head.xaxis.minor_tick_in = 0
		head.yaxis.minor_tick_in = 0
		body.xaxis.minor_tick_in = 0
		body.yaxis.minor_tick_in = 0

		head.xaxis.minor_tick_out = 0
		head.yaxis.minor_tick_out = 0
		body.xaxis.minor_tick_out = 0
		body.yaxis.minor_tick_out = 0

		head.min_border_left = 0
		if index != layout.trail-1:
			head.min_border_right = 0

		head.min_border_top = 0
		head.min_border_bottom = 0

		body.min_border_left = 0
		if index != layout.trail-1:
			body.min_border_right = 0
		body.min_border_top = 0
		# body.min_border_bottom = 0

		head.line((0,20),(10,10))
		head.line((0,20),(20,20))

		heads.append(head)
		bodys.append(body)

	return heads,bodys