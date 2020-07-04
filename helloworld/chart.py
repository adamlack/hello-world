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
        metars_raw = []
        for m in metar_objs:
            metars_raw.append(m.code)
    return metars_raw

@bp.route('/', methods=('GET','POST'))
def index():
    an_icao = request.args.get('icao')
    metars = getLatestMetars(an_icao)
    return render_template('chart/index.html', an_icao=an_icao, metars=metars)