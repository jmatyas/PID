from artiq.experiment import *
import numpy as np

def get_value(mess):

    # function that gets floating point voltages from the user via terminal;
    # it returns that value
    #       mess - message that will be displayed in the console

    while True:
        try:
            variable = float(input(mess))
            return variable
            break
        except ValueError:
            print("The given input wasn't a valid input. Please try again.")
            print("A valid input is a number")


class PID_controller(EnvExperiment):

    # Kp - proportional coefficient
    # Kd - derivative coefficient
    # Ki - integral coefficient
    Kp = 0.0
    Kd = 0.0
    Ki = 0.0
    times = np.arange(6, dtype = np.int64)
    times2 = np.arange(6, dtype = np.int64)
    a = 0.0

    # DAC channel number used in the experiment
    DAC_channel = 0

    def build(self):

        # requesting for devices:
        # core
        # sampler0 - to sample voltages of input (in the end it would be
        #       the output of Phase Detector)
        # zotino0 - to provide (in the end) appropriate output for controlling
        #       LASER/VCO

        self.setattr_device ("core")
        self.setattr_device ("sampler0")
        self.setattr_device ("zotino0")

    def prepare(self):
        self.get_PID_coeffs()

    @kernel
    def run(self):

        # voltages - all 8 channels of ADC are checked at the same time, therefore
        #       8 slots for quantized voltages
        # prop_out - output value of proportinal part of controller
        # derivative_out - output value of derivative part of contreoller
        # integral_in - value of previos measurments and calculations of integral part
        # integrated_out - output value of integral part of controller
        voltages = 0.0
        values = [0.0 for i in range (8)]
        prop_out = 0.0
        derivative_out = 0.0
        integral_in = 0.0
        integrated_out = 0.0
        
        # initial voltages of error coefficient and previous error
        last_error = 0.0

        # initial value of output sum from PID conrolle
        sum = 0.0

        self.initialize_devs()      # initializing devices used in the experiment
        self.core.break_realtime()  # moving time coursor into the future

        
        # while loop in which all the control is done
        # while True:
        self.times[0] = now_mu()
        self.times2[0] = self.core.get_rtio_counter_mu()
        self.sample(values)     # sampling voltages from the PFD
        self.times[1] = now_mu()
        self.times2[1] = self.core.get_rtio_counter_mu()
        delay(400*us)           # delay is needed for sampler to perform its job
        self.times[2] = now_mu()
        self.times2[2] = self.core.get_rtio_counter_mu()
        with parallel:
            prop_out = self.proportional_multiply (values[0], self.Kp)
            integral_in, integrated_out = self.integral_part (values[0], integral_in, self.Ki)
            last_error, derivative_out = self.derivative_part (values[0], last_error, self.Kd)
        self.times[3] = now_mu()
        self.times2[3] = self.core.get_rtio_counter_mu()
        sum = prop_out + integrated_out + derivative_out
        self.times[4] = now_mu()
        self.times2[4] = self.core.get_rtio_counter_mu()
        self.write_output(self.DAC_channel, sum)
        self.times[5] = now_mu()
        self.times2[5] = self.core.get_rtio_counter_mu()

    def analyze(self):
        dtimes = list()
        dtimes2 = list()
        for t in range(5):
            dtimes.append(self.core.mu_to_seconds(self.times[t+1]-self.times[t]))
        
        for t in range(5):
            dtimes2.append(self.core.mu_to_seconds(self.times2[t+1]-self.times2[t]))

        print(dtimes)
        print(dtimes2)

    @kernel
    def initialize_devs(self):

        #  resetting and setting devices

        self.core.reset()
        self.setup_sampler(1)
        self.setup_zotino()

    @kernel
    def setup_sampler(self, gain):

        # initializing sampler - setting each channel's gain to GAIN
        # The four gain settings (0, 1, 2, 3) corresponds to gains of
        # (1, 10, 100, 1000) respectively.

        self.sampler0.init()
        delay(5*ms)
        for i in range(8):
            self.sampler0.set_gain_mu(i, gain)
            delay(100*us) # delay is needed

    @kernel
    def sample(self, values):

        # sampling voltages from Sampler and assigning them to 'voltages'
        self.sampler0.sample(values)

    @kernel
    def setup_zotino (self):
        self.zotino0.init()
        delay(200*us)

    @kernel
    def write_output (self, channel, value):

        # function that allows to output given voltages to DAC
        # in normal operating conditions there should be some delay between
        # different each output, but here sampling and performing floating point
        # calculations in 'run' function gives sufficient time of delay (at least)
        # during the testing it was sufficient). If an underflow error occurs,
        # uncomment delay in the last line

        # saturation of output
        if value >= 10:
            value = 9.99
        elif value <= -10:
            value = -10.0

        # feeds given 'value' to the given channel and outputs it
        self.zotino0.write_dac(channel, value)
        self.zotino0.load()
        # delay(100*us)

    @kernel (flags={"fast-math"})
    def proportional_multiply (self, error, Kp):

        # calculating proportional part of PID based on given voltages

        temp = error * Kp
        return temp

    @kernel (flags={"fast-math"})
    def integral_part (self, error, integral_in, Ki):

        # calculating integral part of PID based on given voltages

        # anti-windup of integration - in case the PID wanted to output higher voltages
        # than DAC is capable of
        temp = integral_in + error
        integrated_out = temp*Ki
        if integrated_out >= 10:
            temp = temp - error
        elif integrated_out <= -10:
            temp = temp - error

        integral_in = temp
        return integral_in, integrated_out

    @kernel (flags={"fast-math"})
    def derivative_part (self, error, last_error, Kd):

        # calculating derivative part of PID based on given voltages

        derivative = error - last_error
        last_error = error
        derivative_out = Kd*derivative
        return last_error, derivative_out

    def get_PID_coeffs(self):

        # getting specified PID's coefficients from the user input

        self.Kp = get_value ("Specify Kp:\n")
        print("Kp = {}".format(self.Kp))
        self.Ki = get_value ("Specify Ki:\n")
        print("Ki = {}".format(self.Ki))
        self.Kd = get_value ("Specify Kd:\n")
        print("Kd = {}".format(self.Kd))
