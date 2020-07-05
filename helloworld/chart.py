from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .get_data import latestMetars, extract
from . import make_plot

bp = Blueprint('chart', __name__, url_prefix='/chart')

@bp.route('/', methods=('GET','POST'))
def index():
    icao = request.args.get('icao')
    metar_data = latestMetars(icao, 12)
    name, units, values, times = extract(metar_data, 'wspeed')
    data={}
    data['Time'] = times
    data[name] = values

    script, div = make_plot.timeLineChart(data, "Time", name, units, icao)

    return render_template('chart/index.html', icao=icao, the_div=div, the_script=script)