import os
from flask import current_app, flash
import xarray as xr
import plotly.offline as py_off
from plotly.graph_objs import *
import numpy as np
from netCDF4 import Dataset
import plotly

MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoibWthbXBmIiwiYSI6ImNqazhpc3MwYzFreWUzd280aW5rbXdiYzAifQ.xpBLEgwNnSUPHL5I--vMTA'

def flash_form_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error: %s" % (
                error
            ), 'error')


class FileHandler:
# For file operations in upload folder

    def __init__(self):
        pass

    def get_uploaded_files(self):
        path = current_app.config['UPLOAD_FOLDER']
        file_list = []
        try:
            raw_list = os.listdir(path)
        except OSError:
            pass
        else:
            for name in raw_list:
                if name.endswith('.nc'):
                    file_list.append(name)
        return file_list


class NcParser:
# For operations with the original NetCDF File

    def __init__(self, filename):
        self.filename = filename
        ncpath = os.path.join(current_app.config['UPLOAD_FOLDER'], self.filename)
        self.dataset = Dataset(ncpath, mode="r")
        self.xarr = xr.open_dataset(xr.backends.NetCDF4DataStore(self.dataset))
        self.dataframe = self.xarr.to_dataframe()

    def get_variables(self):
        ds_vars = []
        for var in self.dataset.variables:
            if var not in self.get_dimensions():
                ds_vars.append(var)
        return ds_vars

    def get_dimensions(self):
        dims = []
        for var in self.dataset.variables:
            for idx, item in enumerate(self.dataset.variables[var].dimensions):
                if self.dataset.variables[var].dimensions[idx] not in dims:
                    dims.append(self.dataset.variables[var].dimensions[idx])
        return dims

    def get_values(self, var_name):
        return self.dataset.variables[var_name][:]

    def get_xarr_values(self, var_name):
        return self.xarr[var_name].values

    def get_file_info(self):
        return self.dataset


class GridMapper:
# For all CRS-related operations

    def __init__(self, subframe):
        self.subframe = subframe

        # All possible grid mapping parameters of CF 1.7 convention
        self.false_easting = None
        self.false_northing = None
        self.longitude_of_projection_origin = None
        self.latitude_of_projection_origin = None
        self.grid_north_pole_latitude = None
        self.grid_north_pole_longitude = None
        self.scale_factor_at_projection_origin = None
        self.scale_factor_at_central_meridian = None
        self.standard_parallel = None
        self.longitude_of_central_meridian = None
        self.straight_vertical_longitude_from_pole = None
        self.perspective_point_height = None


    def read_grid_mapping_info(self):
        # Read info from NC file
        pass

    def set_grid_mapping_info(self):
        # Manually set mapping parameters
        pass

    def transform(self, subframe):
        return subframe




class Plotter:
# For plotting with Pandas Dataframes

    def __init__(self, filename):
        self.filename = filename
        ncpath = os.path.join(current_app.config['UPLOAD_FOLDER'], self.filename)
        self.dataset = Dataset(ncpath, mode="r")
        self.xarr = xr.open_dataset(xr.backends.NetCDF4DataStore(self.dataset))
        self.dataframe = self.xarr.to_dataframe()
        self.north_axis = None
        self.east_axis = None
        self.plotted_var = None
        self.fixed_dim = None
        self.fixed_level = None
        self.scale_factor = 1


    def create_slice(self, transform = False):

        df_sub = self.dataframe.iloc[self.dataframe.index.get_level_values(self.fixed_dim) == self.fixed_level]

        ### Nicht schön, aber funzt...
        to_bin = lambda x: np.floor(x) * self.scale_factor
        ###

        df_sub["latbin"] = df_sub.index.get_level_values(self.north_axis).map(to_bin)
        df_sub["lonbin"] = df_sub.index.get_level_values(self.east_axis).map(to_bin)

        ### TBD sobald Transformtion klappt
        if transform:
            gridmapper = GridMapper(df_sub)
            gridmapper.read_grid_mapping_info()
            df_trans = gridmapper.transform(df_sub)
            df_sub = df_trans
        ###

        df_flat = df_sub.drop_duplicates(subset=['latbin', 'lonbin'])

        # Remove points with NaN values from plot
        df_no_nan = df_flat[np.isfinite(df_flat[self.plotted_var])]
        return df_no_nan


    def plot_slice(self, df_slice, zoom_level):

        data = []
        data.append(
            Scattermapbox(
                lon = df_slice['lonbin'].values,
                lat = df_slice['latbin'].values,
                mode='markers',
                marker=dict(color=df_slice[self.plotted_var].values,
                            showscale=True,
                            ),
                text=df_slice[self.plotted_var].values
            )
        )

        settings = Layout(
            margin=dict(t=0, b=0, r=0, l=0),
            autosize=True,
            hovermode='closest',
            showlegend=False,
            mapbox=dict(
                accesstoken=MAPBOX_ACCESS_TOKEN,
                bearing=0,
                center=dict(
                    lat=0,
                    lon=0
                ),
                pitch=0,
                zoom=zoom_level,
                style='light'
            ),
        )

        fig = dict(data=data, layout=settings)

        config = {'showLink': False}
        div = py_off.plot(fig, config=config, output_type='div')

        return div