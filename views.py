import os
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, current_app, Markup
)
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField
from werkzeug.utils import secure_filename
from importlib.util import spec_from_file_location, module_from_spec

import xarray as xr
from . import models



##### FORMS #####

class PlotSelectForm(FlaskForm):
    plotted_file = SelectField(u'Select File')
    plotted_var = SelectField(u'Select Variable')

class UploadForm(FlaskForm):
    upload = FileField('nc_file', validators=[
        FileRequired(),
        FileAllowed(['nc'], '.nc files only!')
    ])

class FileConfigForm(FlaskForm):
    east_axis = SelectField(u'East Axis')
    north_axis = SelectField(u'North Axis')
    fixed_dimension = SelectField(u'Fixed Dimension')


##### BLUEPRINTS #####
bp = Blueprint('views', __name__, static_folder='static')

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():

    filehandler = models.FileHandler()
    filelist = filehandler.get_uploaded_files()
    form = PlotSelectForm()

    if form.validate_on_submit():
        plotted_view = 'plot/' + form.plotted_file

    return render_template('index.html',filelist=filelist)

@bp.route('/boot', methods=['GET', 'POST'])
def boot():
    return bp.send_static_file('boot/index.html')


@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    file_handler = models.FileHandler()
    file_list = file_handler.get_uploaded_files()

    if form.validate_on_submit():
        file = form.upload.data
        filename = secure_filename(file.filename)
        if filename not in file_list:
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            flash('Successfully uploaded ' + filename)
            return redirect(url_for('views.index'))
        else:
            flash('Upload failed: ' + filename + ' already exists.')
    else:
        models.flash_form_errors(form)

    return render_template('upload.html', form=form)


@bp.route('/config/<filename>', methods=['GET', 'POST'])
def config(filename):
    ncp = models.NcParser(filename)
    form = FileConfigForm()

    dim_options = []
    for dim in ncp.get_dimensions():
        dim_options.append((dim, dim))
    form.east_axis.choices = dim_options
    form.north_axis.choices = dim_options
    form.fixed_dimension.choices = dim_options

    if form.validate_on_submit():

        selected_axes = [form.east_axis.data , form.north_axis.data, form.fixed_dimension.data]
        if len(set(selected_axes)) == len(selected_axes):

            config_file = open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename) + '.config', 'w+')
            config_file.write('selected_axes=' + str(selected_axes) )
            flash('Successfully created ' + filename +'.config')
            return redirect(url_for('views.plot/'+filename))
        else:
            flash('Please select a different variable for each axis')
    else:
        models.flash_form_errors(form)

    return render_template('config.html', form=form)


@bp.route('/samplevienna')
def samplevienna():
    filename = 'ViennaInnerCity_AT_11.00.01_23.06.2017.nc'
    ncp = models.NcParser(filename)
    plotter = models.Plotter(filename)

    plotter.easting = 'nx'
    plotter.northing = 'ny'
    plotter.plotted_var = 'AirTemperature'
    plotter.fixed_dim = 'nz'
    plotter.fixed_level = 2.0
    plotter.scale_factor = 0.005

    df_slice = plotter.create_slice()
    plot = Markup(plotter.plot_slice(df_slice, 5))

    return render_template(
        'mapbox.html',
        plot=plot,
        plotted_var=plotter.plotted_var,
        ds=plotter.dataset,
        df=plotter.dataframe,
        plotter=plotter,
        ds_name=filename,
        ncp=ncp,
        fixed_dim=plotter.fixed_dim,
        fixed_level=plotter.fixed_level
    )


@bp.route('/sampletas')
def sampletas():
    filename = 'sresa1b_ncar_ccsm3-example.nc'
    ncp = models.NcParser(filename)
    plotter = models.Plotter(filename)

    plotter.easting = 'lon'
    plotter.northing = 'lat'
    plotter.plotted_var = 'tas'
    plotter.fixed_dim = 'time'
    plotter.fixed_level = '2000-05-16 12:00:00'

    df_slice = plotter.create_slice()
    plot = Markup(plotter.plot_slice(df_slice, 2))

    return render_template(
        'mapbox.html',
        plot=plot,
        plotted_var=plotter.plotted_var,
        ds=plotter.dataset,
        df=plotter.dataframe,
        ncp=ncp,
        ds_name=filename,
        fixed_dim=plotter.fixed_dim,
        fixed_level=plotter.fixed_level
    )


@bp.route('/sampletasmax')
def sampletasmax():
    filename = 'tasmax_decreg_europe_v20140120_20100801_20100831.nc'
    ncp = models.NcParser(filename)
    plotter = models.Plotter(filename)

    plotter.easting = 'lon'
    plotter.northing = 'lat'
    plotter.plotted_var = 'tasmax'
    plotter.fixed_dim = 'time'
    plotter.fixed_level = '2010-08-26'

    df_slice = plotter.create_slice()
    plot = Markup(plotter.plot_slice(df_slice, 2))

    return render_template(
        'mapbox.html',
        plot=plot,
        plotted_var=plotter.plotted_var,
        ds=plotter.dataset,
        df=plotter.dataframe,
        ncp=ncp,
        ds_name=filename,
        fixed_dim=plotter.fixed_dim,
        fixed_level=plotter.fixed_level
    )


@bp.route('/sampleanom')
def sampleanom():
    filename = 'sst.day.anom.2018.nc'
    ncp = models.NcParser(filename)
    plotter = models.Plotter(filename)

    plotter.easting = 'lon'
    plotter.northing = 'lat'
    plotter.plotted_var = 'anom'
    plotter.fixed_dim = 'time'
    plotter.fixed_level = '2018-01-17'

    df_slice = plotter.create_slice()
    plot = Markup(plotter.plot_slice(df_slice, 2))

    return render_template(
        'mapbox.html',
        plot=plot,
        plotted_var=plotter.plotted_var,
        ds=plotter.dataset,
        df=plotter.dataframe,
        plotter=plotter,
        ncp=ncp,
        ds_name=filename,
        fixed_dim=plotter.fixed_dim,
        fixed_level=plotter.fixed_level
    )


@bp.route('/plot/<filename>/<plotted_var>')
def plot(filename, plotted_var):
    '''
    spec = spec_from_file_location(filename + '.config', 'static/upload/')
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    selected_axes = mod.selected_axes
'''
    selected_axes = ['nx', 'ny', 'nz']
    ncp = models.NcParser(filename)
    plotter = models.Plotter(filename)

    plotter.east_axis = selected_axes[0]
    plotter.north_axis = selected_axes[1]
    plotter.plotted_var = plotted_var
    plotter.fixed_dim = selected_axes[2]
    plotter.fixed_level = 2.0
    plotter.scale_factor = 0.005

    df_slice = plotter.create_slice()
    plot = Markup(plotter.plot_slice(df_slice, 5))

    return render_template(
        'mapbox.html',
        plot=plot,
        plotter=plotter,
        filename=filename,
        ncp=ncp
    )