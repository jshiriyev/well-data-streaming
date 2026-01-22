import copy

from dataclasses import dataclass, field

import os

from bokeh.embed import components

from bokeh.layouts import gridplot

from bokeh.models import Div

# from bokeh.models import CrosshairTool
from bokeh.models import CustomJS
from bokeh.models import HoverTool
from bokeh.models import LinearAxis
from bokeh.models import Label
from bokeh.models import Range1d
from bokeh.models import Span

from bokeh.plotting import figure as bokeh_figure

from bokeh.resources import INLINE

from bokeh.util import browser

from jinja2 import Template

import lasio

import numpy

@dataclass(frozen=True)
class Frame:
	"""Dictionary for general frame construction."""

	width 		: int = 200

	head_sticky : bool = True

	depth_span 	: bool = True

	head_height : int = 60
	body_height : int = 15

	head_xrange : tuple[int] = (0,1) # it is a trail property
	head_yrange	: tuple[int] = (0,1) # it is a trail property

	depth_space : float = 20.

	def __post_init__(self):

		object.__setattr__(
			self,"hrange",(self.head_xrange,self.head_yrange))

class Stream():

	def __init__(self,filename:str,htmlname:str=None,mindepth:float=None,maxdepth:float=None,mnemonics:list=None,**kwargs):

		self.file = lasio.read(filename,**kwargs)

		self.mindepth = mindepth
		self.maxdepth = maxdepth

		self.select(mnemonics)

		self.filename = filename
		self.htmlname = htmlname

		self.spanline = dict(dimension="width",line_width=0.5)

		self.build()

	@property
	def file(self):
		return self._file

	@file.setter
	def file(self,lasfile:lasio.LASFile):
		lasfile.curves = [curve for curve in lasfile.curves if lasfile[curve.mnemonic].dtype == float]
		self._file = lasfile

	@property
	def header(self):
		"""Returns the LASFile with only header section of the original file."""
		file = lasio.LASFile()

		keys = [section for section in self._file.sections if section!="Curves"]

		for key in keys:
			file.sections[key] = self._file.sections[key]

		return file

	@property
	def depths(self):
		return self.file[0]

	@property
	def maxdepth(self):
		return self._maxdepth

	@maxdepth.setter
	def maxdepth(self,value:float):
		self._maxdepth = numpy.nanmax(self.depths) if value is None else value

	@property
	def mindepth(self):
		return self._mindepth

	@mindepth.setter
	def mindepth(self,value:float):
		self._mindepth = numpy.nanmin(self.depths) if value is None else value

	@property
	def depth(self):
		return self.maxdepth-self.mindepth

	def select(self,mnemonics:list):

		if mnemonics is None:
			return

		file = self.header

		mnem = self._file.curves[0].mnemonic

		if mnem in mnemonics:
			mnemonics.remove(mnem)
			
		mnemonics.insert(0,mnem)

		for head in mnemonics:

			curve = self.curve(head)

			file.append_curve(
				curve.mnemonic,curve.data,unit=curve.unit,descr=curve.descr)

		self._file = file
	
	@property
	def htmlname(self):
		return self._htmlname

	@htmlname.setter
	def htmlname(self,value:str):

		if value is None:
			value = self.filename
		
		self._htmlname = os.path.splitext(value)[0]+'.html'

	@property
	def curves(self):
		return len(self.file.keys())-1

	def index(self,key):
		return self._file.keys().index(key)-1

	def curve(self,key):
		return self._file.curves[self.index(key)+1]

	def array(self,key):
		return self.curve(key).data

	@property
	def spanline(self):
		return self._spanline

	@spanline.setter
	def spanline(self,value:dict):
		self._spanline = Span(**value)

	def build(self,wdict:dict=None,**kwargs):

		self.frame = kwargs

		self.width = [self.frame.width]*self.curves

		for key,size in (wdict or {}).items():
			self.width[self.index(key)] = size

		self.lines,self.spanlabels = [],[]

		self.heads = [self.prephead(index) for index in range(1,self.curves+1)]
		self.bodys = [self.prepbody(index) for index in range(1,self.curves+1)]

	@property
	def frame(self):
		return self._frame

	@frame.setter
	def frame(self,value:dict):
		self._frame = Frame(**value)
	
	@property
	def height(self):
		return (self.frame.head_height,self.frame.body_height*int(self.depth))
	
	def prephead(self,index):

		width,height = self.width[index-1],self.height[0]

		if index==1:
			width += int(width/6)

		sticky_css = {'position':'sticky','top':'0px','z-index':'1000'}

		styles = sticky_css if self.frame.head_sticky else {}

		figure = bokeh_figure(width=width,height=height,styles=styles)

		figure = self.boothead(figure,index)
		figure = self.loadhead(figure,index)

		return figure

	def prepbody(self,index):

		width,height = self.width[index-1],self.height[1]

		if index==1:
			width += int(width/6)

		figure = bokeh_figure(width=width,height=height)

		figure = self.bootbody(figure,index)
		figure = self.loadbody(figure,index)

		if self.frame.depth_span:
			figure = self.spanbody(figure,index)

		figure = self.hintbody(figure,index)
			
		return figure

	def boothead(self,figure:bokeh_figure,index:int):

		figure = self.deactivate(figure)

		figure.x_range = Range1d(*self.frame.head_xrange)
		figure.y_range = Range1d(*self.frame.head_yrange)

		figure = self.trim(figure,"x")
		figure = self.trim(figure,"y")

		figure.add_layout(self.bold,'above')
		figure.add_layout(self.bold,'right')

		figure.xgrid.grid_line_color = None
		figure.ygrid.grid_line_color = None

		return figure

	def bootbody(self,figure:bokeh_figure,index:int):

		figure = self.deactivate(figure)

		figure.add_layout(LinearAxis(),'above')

		if index>1:
			figure = self.trim(figure,"y")

		figure.add_layout(self.bold,'right')

		figure.y_range = Range1d(self.maxdepth,self.mindepth)

		figure.yaxis.ticker.max_interval = self.frame.depth_space

		figure.ygrid.minor_grid_line_color = 'lightgray'
		figure.ygrid.minor_grid_line_alpha = 0.2

		figure.ygrid.grid_line_color = 'lightgray'
		figure.ygrid.grid_line_alpha = 1.0

		return figure

	def loadhead(self,figure:bokeh_figure,index:int):

		mnem = self.file.curves[index].mnemonic
		unit = self.file.curves[index].unit

		x = numpy.mean(self.frame.head_xrange)

		ymnem = numpy.quantile(self.frame.head_yrange,0.65)
		yunit = numpy.quantile(self.frame.head_yrange,0.30)

		mnem_label = Label(x=x,y=ymnem,text=mnem,text_font_size='15px',
			text_align='center',text_baseline="middle")

		unit_label = Label(x=x,y=yunit,text=unit,text_font_size='12px',
			text_align='center',text_baseline="middle")

		figure.add_layout(mnem_label)
		figure.add_layout(unit_label)

		return figure

	def loadbody(self,figure:bokeh_figure,index:int):

		self.lines.append(figure.line(self.file[index],self.depths))

		return figure

	def spanbody(self,figure:bokeh_figure,index:int):

		figure.add_layout(self.spanline)

		xmin = numpy.nan if numpy.all(numpy.isnan(self.file[index])) else numpy.nanmin(self.file[index])
		xmax = numpy.nan if numpy.all(numpy.isnan(self.file[index])) else numpy.nanmax(self.file[index])

		# Adding the depth value of spanline as a label
		x = numpy.quantile((xmin,xmax),0.7)

		spanlabel = Label(
			x = x,
			y = 0,
			y_offset = -2.,
			background_fill_color = "white",
			background_fill_alpha = 0.7,
			text = "",
			text_baseline = "top",
			text_align = "left",
			text_font_size = '12px'
			)

		self.spanlabels.append(spanlabel)

		figure.add_layout(spanlabel)

		# Adding move callback to change the location of span depth label.
		figure.js_on_event('mousemove',CustomJS(
			args = dict(label=spanlabel),
			code = """
				const x = cb_obj.x;
				const y = cb_obj.y;
				if (x !== null && y !== null) {
					label.visible = true;
				}
				label.y = y;
				label.text = `${y.toFixed(2)}`;
				"""),
		)

		# Adding leave callback to hide the span when mouse is out of the figure.
		figure.js_on_event('mouseleave',CustomJS(
			args = dict(label=spanlabel),
			code = """label.visible = false;"""),
		)

		return figure

	def hintbody(self,figure:bokeh_figure,index:int):

		xarray = numpy.abs(self.file[index])

		xvalue = numpy.nan if numpy.all(numpy.isnan(xarray)) else numpy.nanmin(xarray[xarray!=0])

		power = 1 if numpy.isnan(xvalue) else -int(numpy.floor(numpy.log10(xvalue)))

		xtips = "@x{0.000}" if power<1 else "@x{0."+"0"*(power+2)+"}"

		dunit = self.file.curves[0].unit

		tooltips = [("",xtips)] if self.frame.depth_span else [("","@y{0.00}" +f"{dunit} : "+xtips)]

		hover = HoverTool(tooltips=tooltips,mode='hline',attachment="above")

		hover.renderers = [self.lines[index-1]]

		if self.frame.depth_span:

			hover.callback = CustomJS(
				args = dict(line=self.spanline),
				code = """
					var geometry = cb_data['geometry'];
					var depth = geometry['y'];
					line.location = depth;
					""",
				)

		figure.add_tools(hover)

		return figure

	def mapline(self,key:str,**kwargs):

		for name,value in kwargs.items():
			setattr(self.lines[self.index(key)].glyph,f"line_{name}",value)

	def color(self,key:str,cut:float,left:bool=True,**kwargs):

		conds = self.array(key)<cut if left else self.array(key)>cut

		z1 = numpy.where(conds,self.array(key),cut)
		z2 = numpy.full_like(z1,cut)

		x1 = z1 if left else z2
		x2 = z2 if left else z1

		self.bodys[self.index(key)].harea(y=self.depths,x1=x1,x2=x2,**kwargs)

	def limit(self,key:str,xlim:tuple=None,*,xmin:float=numpy.nan,xmax:float=numpy.nan):

		xlim = (xmin,xmax) if xlim is None else xlim

		index = self.index(key)

		self.bodys[index].x_range.start = xlim[0]
		self.bodys[index].x_range.end = xlim[1]

		xmin = numpy.nanmin(self.file[index]) if numpy.isnan(xlim[0]) else xlim[0]
		xmax = numpy.nanmax(self.file[index]) if numpy.isnan(xlim[1]) else xlim[1]

		self.spanlabels[index].x = numpy.quantile((xmin,xmax),0.7)

	def overlay(self,key:str,tokey:str,multp:float=1,shift:float=0,line:dict=None,left:bool=None,**kwargs):

		value = self.array(key)*multp+shift

		style = {f"line_{name}":value for name,value in (line or {}).items()}

		self.bodys[self.index(tokey)].line(value,self.depths,**style)

		if left is None:
			return

		conds = value<self.array(tokey) if left else value>self.array(tokey)

		z1 = numpy.where(conds,value,self.array(tokey))
		z2 = numpy.full_like(z1,self.array(tokey))

		x1 = z1 if left else z2
		x2 = z2 if left else z1

		self.bodys[self.index(tokey)].harea(y=self.depths,x1=x1,x2=x2,**kwargs)

	def maptops(self,topdict:dict,**kwargs):

		linemap = {f"line_{key}":value for key,value in kwargs.items()}

		for index in range(1,self.curves+1):
			if not numpy.all(numpy.isnan(self.file[index])):
				break

		xmin = numpy.nan if numpy.all(numpy.isnan(self.file[index])) else numpy.nanmin(self.file[index])
		xmax = numpy.nan if numpy.all(numpy.isnan(self.file[index])) else numpy.nanmax(self.file[index])

		x = numpy.quantile((xmin,xmax),0.5)

		for key,value in topdict.items():

			formation_top_span = Span(location=value,dimension='width',**linemap)

			for body in self.bodys:
			    body.add_layout(formation_top_span)

			formation_top_name = Label(x=x,y=value,
				y_offset = -3.,
				background_fill_color = "white",
				background_fill_alpha = 0.7,
				text = key,
				text_baseline = "top",
				text_align = "center",
				text_font_size = '14px',
				text_font_style = "bold"
				)

			self.bodys[index-1].add_layout(formation_top_name)

	@staticmethod
	def deactivate(figure:bokeh_figure):

		figure.toolbar.active_drag = None
		figure.toolbar.active_scroll = None
		figure.toolbar.active_tap = None

		return figure

	@staticmethod
	def trim(figure:bokeh_figure,axis="x"):

		getattr(figure,f"{axis}axis").major_tick_line_alpha = 0
		getattr(figure,f"{axis}axis").minor_tick_line_alpha = 0
		getattr(figure,f"{axis}axis").major_label_text_alpha = 0

		return figure

	def wrapup(self):

		grid = gridplot([self.heads,self.bodys],toolbar_location=None)

		script,div = components(grid)

		return self.template.render(
			java=self.java,css=self.css,script=script,div=div)

	@property
	def template(self):
		return Template(
			'''
			<!DOCTYPE html>
			<html lang="en">
				<head>
					<meta charset="utf-8">
					<title>LAS Curves - Bokeh Glance</title>
					{{ java }}
					{{ css }}
					{{ script }}
				<style>
				.wrapper {
					display: flex;
					justify-content: center;
					align-items: center;
					margin: 0 auto;
					}
				.plotdiv {
					margin: 0 auto;
					}
				</style>
				</head>
				<body>
				<div class='wrapper'>
					{{ div }}
				</div>
				</body>
			</html>
			'''
			)

	@property
	def bold(self):
		return LinearAxis(
			major_tick_line_alpha=0,
			minor_tick_line_alpha=0,
			major_label_text_alpha=0,
			)

	@property
	def java(self):
		return INLINE.render_js()

	@property
	def css(self):
		return INLINE.render_css()

	def show(self):

		htmltext = self.wrapup()

		with open(self.htmlname,'w') as htmlfile:
			htmlfile.write(htmltext)

		browser.view(self.htmlname)