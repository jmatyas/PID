from artiq.experiment import *
from artiq.coredevice.ad53xx import voltage_to_mu
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
    a = np.int64()

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
        values = [0 for i in range (8)]
        error_sig = 0.0
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
        self.sample(values)     # sampling voltages from the PFD - it needs more or less 230 us
        error_sig = float(values[0])
        delay(200*us)           # delay is needed for sampler to perform its job
        with parallel:
            prop_out = self.proportional_multiply (error_sig, self.Kp)
            integral_in, integrated_out = self.integral_part (error_sig, integral_in, self.Ki)
            last_error, derivative_out = self.derivative_part (error_sig, last_error, self.Kd)
        # calculations above take approximately 40 us
        sum = prop_out + integrated_out + derivative_out    # it takes around 0.5 us
        self.write_output(self.DAC_channel, int(sum)+32768) # it takes around 30 us
    
    # summary: 230+40 + 30 = 300 us; 3300 Hz bandwidth

    # def analyze(self):
    #     print(voltage_to_mu(9.99))
    #     print(voltage_to_mu(-10.))
    #     dtimes2 = list()
        
    #     for t in range(len(self.times)-1):
    #         dtimes2.append(self.core.mu_to_seconds(self.times2[t+1]-self.times2[t]))

    #     print(dtimes2)

    @kernel
    def initialize_devs(self):

        #  resetting and setting devices

        self.core.reset()
        self.setup_sampler(0)
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
        self.sampler0.sample_mu(values)

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
        if value >= voltage_to_mu(9.99):
            value = voltage_to_mu(9.99)
        elif value <= voltage_to_mu(-10.):
            value = voltage_to_mu(-10.)

        # feeds given 'value' to the given channel and outputs it
        self.zotino0.write_dac_mu(channel, value)
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
        if integrated_out >= voltage_to_mu(9.99)- 32768.0:
            temp = temp - error
        elif integrated_out <= voltage_to_mu(-10.) - 32768.0:
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
