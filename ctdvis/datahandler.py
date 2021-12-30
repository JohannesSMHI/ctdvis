# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-07-03 11:24

@author: a002028
"""
from abc import ABC
import os

import pandas as pd
import numpy as np
from ctdpy.core.session import Session
from ctdpy.core.utils import generate_filepaths

from ctdvis.filter import Filter


def set_color_code(qf):
    """Return color based on the given flag."""
    if qf == 'B':
        return 'red'
    elif qf == 'S':
        return 'orange'
    elif qf == 'E':
        return 'green'
    else:
        return 'navy'


class Datadict(dict):
    """Data Dictionary.

    We intend to use filenames as keys with profile dataframes as items.
    """

    def __init__(self, data_directory=None):
        """Initiate."""
        super().__init__()
        self.data_directory = data_directory

    def load_data(self, return_session=False, filters=None):
        """Load CTD-standard-formnat data.

        Using ctdpy.

        Args:
            return_session (bool): True/False
            filters (dict | None): Filter out files to load based on month, serno or ship.
        """
        files = generate_filepaths(self.data_directory,
                                   pattern='ctd_profile_',
                                   endswith='.txt',
                                   only_from_dir=True)

        files = list(files)

        if filters:
            filter_obj = Filter([os.path.basename(f) for f in files])
            filter_obj.add_filter(**filters)
            files = [f for f in files if os.path.basename(f) in filter_obj.valid_file_names]

        ctd_session = Session(filepaths=files, reader='ctd_stdfmt')

        datasets = ctd_session.read()

        for key, item in datasets[0].items():
            self.append_item(key, item)

        if return_session:
            return ctd_session

    def append_item(self, key, item):
        """Append item to self."""
        print('Appending data for key: {}'.format(key))
        self.setdefault(key, item)


class Frame(pd.DataFrame, ABC):
    """Subclassing pandas.DataFrame.

    We intend to use Frame as a DataFrame for all selected profile dataset.
    """

    @property
    def _constructor(self):
        """Construct DataFrame, overides method in pd.DataFrame."""
        return Frame

    def convert_formats(self):
        """Convert hard coded formats."""
        self['SDATE'] = self[['YEAR', 'MONTH', 'DAY']].astype(str).apply('-'.join, axis=1)
        self['STIME'] = self[['HOUR', 'MINUTE']].astype(str).apply(':'.join, axis=1)

    def set_column_format(self, **kwargs):
        """Set dtype of each parameter in the dataframe."""
        for key, value in kwargs.items():
            if key in self.columns:
                try:
                    self[key] = self[key].astype(value)
                    if value == str:
                        self[key] = self[key].replace('nan', '')
                except ValueError:
                    self[key] = self[key].replace('', np.nan).astype(value)

    def add_color_columns(self, q_params, mapper=None):
        """Add color columns for each parameter."""
        for q_para in q_params:
            color_key = mapper.get(q_para)
            self[color_key] = np.vectorize(set_color_code)(self[q_para].fillna(''))


class DataHandler:
    """Handler of data formats.

    Stores rawdata (ctd-standard-format).
    Appends selected filtered datasets (self.raw_data) to Frame (self.df).
    Conform self.df in order to use it in bokeh tools.
    """

    def __init__(self, filters):
        """Initiate."""
        self.filters = filters
        self.raw_data = Datadict()
        self.df = Frame(index=[])
        self.ctd_session = None

    def load_profile_data(self, directory):
        """Load data."""
        self.raw_data.data_directory = directory
        self.ctd_session = self.raw_data.load_data(return_session=True, filters=self.filters)

    def construct_dataframe(self, settings):
        """Set up dataframe according to a bokeh friendly format."""
        for key, item in self.raw_data.items():
            df = item['data'].copy()
            df['KEY'] = key.strip('ctd_profile|.txt')
            self.df = self.df.append(Frame(df))

        self.df.reset_index(drop=True, inplace=True)
        self.df.convert_formats()
        self.df.add_color_columns(settings.q_parameters, mapper=settings.q_colors_mapper)
        self.df.set_column_format(**settings.parameter_formats)
        self.check_columns(*settings.meta_parameters)

    def check_columns(self, *args):
        """Add columns that are not present in the dataframe."""
        for col in args:
            if col not in self.df:
                self.df[col] = ''
