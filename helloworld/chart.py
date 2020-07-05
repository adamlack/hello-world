from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

import requests
from metar import Metar
import datetime
import re

bp = Blueprint('chart', __name__, url_prefix='/chart')

def cleanOgi(input):
    p = map(lambda i: i.split(), input)
    output = []
    i = 0
    for l in p:
        temp = map(lambda s: s.strip('\\n'), l)
        output.append(' '.join(list(map(lambda t: t.strip('='), temp))[1:]))
        i = i+1
    return output

def getLatestMetars(icao):
    #Get last 6 hours of metars
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(hours=6)
    s = start.strftime('&ano=%Y&mes=%m&day=%d&hora=%H&min=%M')
    e = end.strftime('&anof=%Y&mesf=%m&dayf=%d&horaf=%H&minf=%M')
    out = None
    urlstring = 'http://ogimet.com/display_metars2.php?lang=en&lugar='+str(icao)+'&tipo=ALL&ord=REV&nil=NO&fmt=txt'+s+e+'&send=send'
    response = requests.get(urlstring)
    if response is not None:
        page = response.text.replace('\n','')
        page = ' '.join(page.split())
        rex = '(METAR .*?=)'
        metars = re.findall(rex, str(page))
        metars = cleanOgi(metars)
        metar_objs = []
        for m in metars:
            metar_objs.append(Metar.Metar(m, strict=False))
        metars_val, times = [],[]
        for m in metar_objs:
            metars_val.append(m.wind_speed.value('KT'))
            times.append(m.time)
    return metars_val, times

from bokeh.models import (HoverTool, Plot, LinearAxis, Grid, Range1d)
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource

def create_hover_tool():
    return None

def create_the_chart(data, title, x_name, y_name, width=600, height=300):
    source = ColumnDataSource(data)
    xdr, ydr = Range1d(start=0,end=max(data[x_name])), Range1d(start=0,end=max(data[y_name]))
   
    plot = figure(title=title, plot_width=width,
                    plot_height=height, x_axis_type='datetime')

    plot.line(x='Time', y='Value', source=data)
    plot.add_tools(HoverTool(tooltips='<span style="background:#f00;">The value here is @Value</span>',mode='vline'))

    return plot

@bp.route('/', methods=('GET','POST'))
def index():
    an_icao = request.args.get('icao')
    metars, times = getLatestMetars(an_icao)
    data = {'Time':times,'Value':metars}

    hover = create_hover_tool()
    plot = create_the_chart(data, "Titluar phrase", "Time", "Value")
    script, div = components(plot)

    return render_template('chart/index.html', an_icao=an_icao, metars=metars, the_div=div, the_script=script)