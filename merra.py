import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap, HeatMapWithTime
from netCDF4 import Dataset
import cartopy.crs as ccrs
from os.path import exists

import requests # get the requsts library from https://github.com/requests/requests

# overriding requests.Session.rebuild_auth to mantain headers when redirected

class SessionWithHeaderRedirection(requests.Session):

    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

   # Overrides from the library to keep headers when redirected to or from

   # the NASA auth host.

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and redirect_parsed.hostname != self.AUTH_HOST and original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']

        return

def plot(session, filename, year, month, plot_type):

    data = Dataset(filename, more="r")
    lons = data.variables['lon'][:]
    lats = data.variables['lat'][:]
    time = data.variables['time'][:]
    COCL = data.variables['COCL'][:,:,:]; COCL = COCL[0,:,:]
    COEM = data.variables['COEM'][:,:,:]; COEM = COEM[0,:,:]
    COLS = data.variables['COLS'][:,:,:]; COLS = COLS[0,:,:]
    TO3 =  data.variables['TO3'][:,:,:];  TO3 =  TO3[0,:,:]

    plot_types = {
            'COCL': COCL,
            'COEM': COEM,
            'COLS': COLS,
            'TO3': TO3
            }

    def plot_merra_data(data, title='', date='April 2020'):
        fig = plt.figure(figsize=(16,8))
        ax = plt.axes(projection=ccrs.Robinson())
        ax.set_global()
        ax.coastlines(resolution="110m",linewidth=1)
        ax.gridlines(linestyle='--',color='black')
        plt.contourf(lons, lats, data, transform=ccrs.PlateCarree(),cmap=plt.cm.jet)
        plt.title(f'MERRA-2 {title} levels, {date}', size=14)
        cb = plt.colorbar(ax=ax, orientation="vertical", pad=0.02, aspect=16, shrink=0.8)
        cb.set_label('K',size=12,rotation=0,labelpad=15)
        cb.ax.tick_params(labelsize=10)
        print("Saving the plot")
        fname = f"plot_{filename}.png"
        plt.savefig(fname)
        return fname

    return plot_merra_data(plot_types[plot_type], plot_type, date = f"{year} {month}")
    #return fname
    #plot_merra_data(COEM, 'COEM')
    #plot_merra_data(COLS, 'COLS')
    #plot_merra_data(TO3, 'TO3')

def download_nc4(session, year,month, plot_type='COCL'):

    if plot_type not in {'COCL', 'COLS', 'COEM', 'TO3'}:
        raise ValueError('plot', 'Invalid plot type')

    # the url of the file we wish to retrieve
    url = f"https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2_MONTHLY/M2TMNXCHM.5.12.4/{year}/MERRA2_400.tavgM_2d_chm_Nx.{year}{month}.nc4.nc4"

    print(url)
    # extract the filename from the url to be used when saving the file

    try:

        # save the file

        filename = f"{year}_{month}.nc4"

        if not exists(filename):
            # submit the request using the session

            # raise an exception in case of http errors
            response = session.get(url, stream=True)
            print(response.status_code, type(response.status_code))

            if response.status_code == 404:
                raise ValueError('date', 'Invalid year or month')
            with open(filename, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    fd.write(chunk)

        print(filename)

        plot_file = plot(session, filename, year, month, plot_type)

        return plot_file

    except requests.exceptions.HTTPError as e:
        print(e)
        return "Connection error", 500
    except requests.exceptions.ConnectionError:
        return "Connection error", 500

#download_nc4('2018', '11')
