# Copyright (c) 2017 LSD - UFCG.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ConfigParser

from service.api.controller.plugins.basic.controller import Basic_Controller
from service.api.controller.metric_source_builder import Metric_Source_Builder
from service.api.actuator.actuator_builder import Actuator_Builder
from service.api.controller.plugins.single_application_controller import Single_Application_Controller
from service.api.controller.plugins.generic.controller import Generic_Controller
from service.api.controller.plugins.tendency.controller import (
    Tendency_Aware_Proportional_Controller
)
from service.api.controller.plugins.proportional.controller import Proportional_Controller
from service.api.controller.plugins.proportional_derivative.controller import (
    ProportionalDerivativeController
)
from service.api.controller.plugins.pid.controller import PIDController
from abc import ABCMeta
from abc import abstractmethod
from service.api.controller.controller_builder import Controller_Builder
import threading
from utils.logger import Log, configure_logging


'''
The Controller is the component responsible for, based on metrics of infrastructure and application
health such as application progress and CPU usage, taking actions to ensure compliance with
quality of service levels.
'''


class Controller:
    __metaclass__ = ABCMeta

    '''
        Creates a Controller instance.

        app_id is the id of the application associated with the instance.
        parameters is a dictionary of scaling parameters.
    '''
    @abstractmethod
    def __init__(self, app_id, parameters):
        pass

    '''
        Starts scaling for the application associated
        with the controller instance. The method is not expected
        to return until the scaling is stopped through the
        stop_application_scaling. Normally, this method is used
        as a run method by a thread.
    '''
    @abstractmethod
    def start_application_scaling(self):
        pass

    '''
        Stops scaling for the application associated
        with the controller instance. This method's expected
        side effect is to make start_application_scaling to return.
    '''
    @abstractmethod
    def stop_application_scaling(self):
        pass

    '''
        Returns information on the status of the scaling of applications,
        normally as a string.
    '''
    @abstractmethod
    def status(self):
        pass


class Main_Controller:

    def __init__(self):
        self.logger = Log("main.controller.log", "controller.log")
        configure_logging()

        self.controller_thread_pool = {}
        self.controller_builder = Controller_Builder()

    def start_application_scaling(self, application_id, parameters):
        self.logger.log("Adding application id: %s" % (application_id))
        plugin_name = parameters["scaler_plugin"]
        controller = self.controller_builder.get_controller(plugin_name, application_id, parameters)
        controller_thread = threading.Thread(target=controller.start_application_scaling)
        controller_thread.start()

        self.controller_thread_pool[application_id] = controller

    def stop_application_scaling(self, app_id):
        if app_id in self.controller_thread_pool.keys():
            self.logger.log("Removing application id: %s" % (app_id))
            app_controller = self.controller_thread_pool[app_id]
            app_controller.stop_application_scaling()
            self.controller_thread_pool.pop(app_id)
        else:
            self.logger.log("Application %s not found" % (app_id))

    def status(self):
        status_string = "Status: OK\n"
        status_string += "Monitoring applications:\n"
        for application_id in self.controller_thread_pool.keys():
            status_string += application_id + "\n"
            status_string += "Last action:" + self.controller_thread_pool[application_id].status()
            status_string += "\n"

        return status_string


class Controller_Builder:

    def __init__(self):
        pass

    def get_controller(self, name, application_id, parameters):
        if name == "basic":
            config = ConfigParser.RawConfigParser()
            config.read("controller.cfg")

            # Read scaling policy
            metric_source_type = config.get("policy", "metric_source")
            actuator_type = config.get("policy", "actuator")

            # Read configuration
            check_interval = config.getfloat("scaling", "check_interval")
            trigger_down = config.getfloat("scaling", "trigger_down")
            trigger_up = config.getfloat("scaling", "trigger_up")
            min_cap = config.getfloat("scaling", "min_cap")
            max_cap = config.getfloat("scaling", "max_cap")
            actuation_size = config.getfloat("scaling", "actuation_size")
            metric_rounding = config.getint("scaling", "metric_rounding")

            parameters = {"check_interval": check_interval, "trigger_down": trigger_down,
                          "trigger_up": trigger_up, "min_cap": min_cap, "max_cap": max_cap,
                          "actuation_size": actuation_size, "metric_rounding": metric_rounding}

            metric_source = Metric_Source_Builder().get_metric_source(metric_source_type)
            actuator = Actuator_Builder().get_actuator(actuator_type)

            return Basic_Controller(metric_source, actuator, parameters)
        elif name == "single":
            return Single_Application_Controller(application_id, parameters)
        elif name == "progress-error":
            return Generic_Controller(application_id, parameters)
        elif name == "proportional":
            return Proportional_Controller(application_id, parameters)
        elif name == "proportional_derivative":
            return ProportionalDerivativeController(application_id, parameters)
        elif name == "pid":
            return PIDController(application_id, parameters)
        elif name == "progress-tendency":
            return Tendency_Aware_Proportional_Controller(application_id, parameters)
        else:
            # FIXME: exception type
            raise Exception("Unknown controller type")