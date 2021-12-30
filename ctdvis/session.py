# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-07-03 11:24

@author: a002028
"""
from ctdvis.config import Settings
from ctdvis.tools.quality_control import QCWorkTool
from ctdvis.datahandler import DataHandler


class Session:
    """Main class of ctdvis."""

    def __init__(self, visualize_setting=None, data_directory=None, filters=None):
        """Initiate."""
        self.data_directory = data_directory
        self.settings = Settings(visualize_setting=visualize_setting)

        self.dh = DataHandler(filters)

    def setup_datahandler(self):
        """Load data and set up the dataframe to use."""
        self.dh.load_profile_data(self.data_directory)
        self.dh.construct_dataframe(self.settings)

    def run_tool(self, tool='qc_smhi', return_layout=False):
        """Run the main QC tool (Bokeh)."""
        # TODO settings in yaml-files.. dynamic obj-load..
        plot = QCWorkTool(
            self.dh.df[self.settings.selected_keys],
            datasets=self.dh.raw_data,
            parameters=self.settings.data_parameters_with_units,
            plot_parameters_mapping=self.settings.plot_parameters_mapping,
            plot_keys=self.settings.plot_keys,
            color_fields=self.settings.q_colors,
            qflag_fields=self.settings.q_parameters,
            auto_q_flag_parameters=self.settings.q0_plot_keys,
            ctdpy_session=self.dh.ctd_session,
            multi_sensors=self.settings.multi_sensors,  # IMPORTANT!!! SMHI HAS MULTIPLE TEMP, SALT, DOXY SENSORS
            combo_plots=self.settings.combo_plots,
            user_download_directory=self.settings.user_download_directory,
        )
        plot.plot_stations()
        plot.plot_data()

        if return_layout:
            return plot.return_layout()
