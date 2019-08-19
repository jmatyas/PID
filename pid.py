from artiq.experiment import *


def get_value(mess):
    while True:
        try:
            variable = float(input(mess))
            return variable
            break
        except ValueError:
            print("The given input wasn't a valid input. Please try again.")
            print("A valid input is a number")


class PID_controller(EnvExperiment):

    # values - all 8 channels of ADC are checked at the same time, therefore
    #       8 slots for quantized VALUES
    # prop_out - output value of proportinal part of controller
    # derivative_out - output value of derivative part of contreoller
    # integral_in - value of previos measurments and calculations of integral part
    # integrated_out - output value of integral part of controller
    values = [0.0 for i in range (8)]
    prop_out = 0.0
    derivative_out = 0.0
    integral_in = 0.0
    integrated_out = 0.0

    # Kp - proportional coefficient
    # Kd - derivative coefficient
    # Ki - integral coefficient
    Kp = 0.0
    Kd = 0.0
    Ki = 0.0

    # DAC channel number used in the experiment
    DAC_channel = 1

    last_error = 0.0
    err_coeff = 0.0

    sum = 0.0

    def build(self):
        # requesting for devices:
        # core
        # sampler0 - to sample values of input (in the end it would be
        #       the output of Phase Detector)
        # zotino0 - to provide (in the end) appropriate output for controlling
        #       LASER/VCO

        self.setattr_device ("core")
        self.setattr_device ("sampler0")
        self.setattr_device ("zotino0")

    @kernel
    def run(self):
        #  resetting and setting devices

        self.core.reset()
        self.setup_sampler(0)
        self.setup_zotino()
        self.get_PID_coeffs()
        self.core.break_realtime() # moving time coursor into the future

        # while loop in which all the control is done
        while True:
            self.sample(self.values)
            if self.values[0] > 0.5 :
                self.err_coeff = 1.0
            else:
                self.err_coeff = -1.0

            self.proportional_multiply(self.err_coeff, self.Kp, self.prop_out)
            self.integral_part(self.err_coeff, self.Ki, self.integral_in, self.integrated_out )
            self.derivative_part(self.err_coeff, self.last_error, self.Kd, self.derivative_out)

            sum = self.prop_out + self.derivative_out + self.integrated_out

            # self.core.break_realtime()
            self.write_output(self.DAC_channel, self.sum)


    @kernel
    def setup_sampler(self, gain):
        # initializing sampler - setting each channel's gain to GAIN
        self.sampler0.init()
        for i in range(8):
            self.sampler0.set_gain_mu(i, gain)
            delay(100*us) # delay is needed (for some reason)

    @kernel
    def sample(self, values):
        self.sampler0.sample(values)

    @kernel
    def setup_zotino (self):
        self.zotino0.init()

    @kernel
    def write_output (self, channel, value):
        if value > 10:
            value = 10.0
        elif value < -10:
            value = -10.0

        self.zotino0.write_dac(channel, value)
        self.zotino0.load()

    @kernel
    def proportional_multiply (self, error, Kp, proportional_output):
        proportional_output = error * Kp

    @kernel
    def integral_part (self, error, Ki, integral_in, integrated_out):
        temp = integral_in + error
        integrated_out = Ki*temp
        integral_in = temp

    @kernel
    def derivative_part (self, error, last_error, Kd, derivative_out):
        derivative = error - last_error
        last_error = error
        derivative_out = Kd*derivative

    def get_PID_coeffs(self):
        self.Kp = get_value ("Specif Kp:\n")
        print(self.Kp)
        self.Ki = get_value ("Specify Ki:\n")
        print(self.Ki)
        self.Kd = get_value ("Specify Kd:\n")
        print(self.Kd)
