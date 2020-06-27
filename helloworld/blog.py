from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from helloworld.auth import login_required
from helloworld.db import get_db

import requests
from metar import Metar
import datetime
import re

bp = Blueprint('blog', __name__)

def cleanOgi(input):
    p = map(lambda i: i.split(), input)
    output = []
    i = 0
    for l in p:
        temp = map(lambda s: s.strip('\\n'), l)
        output.append(' '.join(list(map(lambda t: t.strip('='), temp))[1:]))
        i = i+1
    return output

def getLatestMetar():
    icao = 'EGVO'
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(hours=1)
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
        out = Metar.Metar(metars[0], strict=False)
    return out.code

import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def plotView(icao):
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title(icao)
    axis.set_xlabel('x axis')
    axis.set_ylabel('y axis')
    axis.grid()
    axis.plot(range(5), range(5), 'ro-')

    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)

    pngImageB64String = 'data:image/png;base64,'
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    return pngImageB64String

@bp.route('/', methods=('GET','POST'))
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    an_icao = request.args.get('icao')
    return render_template('blog/index.html', posts=posts, ametar=getLatestMetar(), image=plotView(an_icao))

@bp.route('/create', methods=('GET','POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)', (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id WHERE p.id = ?', (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post

@bp.route('/<int:id>/update', methods=('GET','POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?', (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))