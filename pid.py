from artiq.experiment import *

values = [[0.0 for i in range (8)] for j in range (10)]

class PID_controller(EnvExperiment):
    def build(self):
        self.setattr_device ("core")
        self.setattr_device ("sampler0")

    @kernel
    def run(self):
        self.core.reset()
        self.setup_sampler(0)
        self.core.break_realtime()

        self.sample(500, values)


    @kernel
    def setup_sampler(self, gain):
        self.sampler0.init()
        for i in range(8):
            self.sampler0.set_gain_mu(i, gain)
            delay(100*us)

    @kernel
    def sample(self, delayPeriod, values):
        for measures in range (len(values)):
            self.sampler0.sample(values[measures])
            delay(delayPeriod*us)
        for measure in range (len(values)):
            print(values[measure][0])
