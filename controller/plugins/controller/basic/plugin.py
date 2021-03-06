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

import threading
import time

from controller.plugins.controller.basic.alarm import BasicAlarm
from controller.plugins.controller.base import Controller
from controller.utils.logger import Log, configure_logging


# FIXME: This class does not work with the current scaler format.
# It should be removed in the future.
class BasicController(Controller):

    def __init__(self, metric_source, actuator, plugin_info):
        # Set up logging
        self.logger = Log("basic.controller.log", "controller.log")
        configure_logging()

        check_interval = plugin_info["check_interval"]
        trigger_down = plugin_info["trigger_down"]
        trigger_up = plugin_info["trigger_up"]
        min_cap = plugin_info["min_cap"]
        max_cap = plugin_info["max_cap"]
        actuation_size = plugin_info["actuation_size"]
        metric_rounding = plugin_info["metric_rounding"]

        # Start alarm
        self.alarm = BasicAlarm(actuator, metric_source, trigger_down,
                                trigger_up, min_cap, max_cap, actuation_size,
                                metric_rounding)

        # Start up controller thread
        # Create lock to access application list
        self.applications_lock = threading.RLock()
        self.applications = {}
        self.controller = _BasicControllerThread(
            self.applications, self.applications_lock, self.alarm,
            check_interval)

        self.controller_thread = threading.Thread(target=self.controller.start)
        self.controller_thread.start()

    def start_application_scaling(self, app_id, plugin_info):
        self.logger.log("Adding application id: %s" % (app_id))
        # Acquire lock and add application
        with self.applications_lock:
            self.applications[app_id] = plugin_info

    def stop_application_scaling(self, app_id):
        #  Acquire lock and remove application
        with self.applications_lock:
            if app_id in self.applications.keys():
                self.logger.log("Removing application id: %s" % (app_id))
                self.applications.pop(app_id)
            else:
                self.logger.log("Application %s not found" % (app_id))

    def stop_controller(self):
        self.controller.running = False

    def status(self):
        return ""


class _BasicControllerThread():

    def __init__(self, applications, applications_lock, alarm, check_interval):
        self.logger = Log("basic.controller_thread.log", "controller.log")
        configure_logging()

        self.applications = applications
        self.applications_lock = applications_lock
        self.alarm = alarm
        self.check_interval = check_interval
        self.running = True

    def start(self):
        self.logger.log("Starting controller thread")

        while self.running:
            # acquire lock, check applications and wait
            with self.applications_lock:
                self.logger.log("Monitoring applications: %s" %
                                (str(self.applications.keys())))

                applications_ids = self.applications.keys()

                # for each application check state
                for application_id in applications_ids:
                    instances = self.applications[application_id]["instances"]

                    self.logger.log("Checking application:%s|instances:%s" % (
                        application_id, instances))

                    self.alarm.check_application_state(
                        application_id, instances)

            time.sleep(float(self.check_interval))
