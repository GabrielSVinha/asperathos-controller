import threading
import time
import unittest

from mock.mock import MagicMock
from service.api.controller.plugins.single_application_controller import Single_Application_Controller


class Test_Single_Application_Controller(unittest.TestCase):

    def setUp(self):
        self.app_id_0 = "app-00"
        self.parameters = {}
        
        self.instance_1 = "instance-1"
        self.instance_2 = "instance-2"
        self.instances = [self.instance_1, self.instance_2]
        
        self.check_interval = 2
        self.trigger_down = 10
        self.trigger_up = 100
        self.min_cap = 10
        self.max_cap = 100
        self.actuation_size = 20
        self.metric_rounding = 2
        self.actuator = "basic"
        self.metric_source = "nop"
        
        self.parameters["instances"] = self.instances
        self.parameters["check_interval"] = self.check_interval
        self.parameters["trigger_down"] = self.trigger_down
        self.parameters["trigger_up"] = self.trigger_up
        self.parameters["min_cap"] = self.min_cap
        self.parameters["max_cap"] = self.max_cap
        self.parameters["actuation_size"] = self.actuation_size
        self.parameters["metric_rounding"] = self.metric_rounding
        self.parameters["actuator"] = self.actuator
        self.parameters["metric_source"] = self.metric_source
        
        self.controller = Single_Application_Controller(self.app_id_0, self.parameters)

    def test_start_and_stop_scaling(self):
        self.controller.alarm.check_application_state = MagicMock(return_value=None)
        
        controller_thread = threading.Thread(target=self.controller.start)
        controller_thread.start()

        time.sleep(float(2*self.check_interval))

        self.controller.alarm.check_application_state.assert_any_call(self.app_id_0, self.instances)
        
        self.controller.stop()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()