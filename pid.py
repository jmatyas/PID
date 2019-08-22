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

    # Kp - proportional coefficient
    # Kd - derivative coefficient
    # Ki - integral coefficient
    Kp = 0.0
    Kd = 0.0
    Ki = 0.0

    # DAC channel number used in the experiment
    DAC_channel = 0

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

    def prepare(self):
        self.get_PID_coeffs()

    @kernel
    def run(self):
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


        # initial values of error coefficient and previous error
        last_error = 0.0

        # initial value of output sum from PID conrolle
        sum = 0.0

        #  resetting and setting devices
        self.core.reset()
        self.setup_sampler(0)
        self.setup_zotino()
        self.core.break_realtime() # moving time coursor into the future
        # while loop in which all the control is done\
        while True:
            self.sample(values)             # sampling values from the PFD
            delay(300*us)
            prop_out = self.proportional_multiply (values[0], self.Kp)
            integral_in, integrated_out = self.integral_part (values[0], integral_in, self.Ki)
            last_error, derivative_out = self.derivative_part (values[0], last_error, self.Kd)

            sum = prop_out + integrated_out + derivative_out
            self.write_output(self.DAC_channel, sum)

    @kernel
    def setup_sampler(self, gain):
        # initializing sampler - setting each channel's gain to GAIN
        self.sampler0.init()
        delay(5*ms)
        for i in range(8):
            self.sampler0.set_gain_mu(i, gain)
            delay(100*us) # delay is needed (for some reason)

    @kernel
    def sample(self, values):
        self.sampler0.sample(values)

    @kernel
    def setup_zotino (self):
        self.zotino0.init()
        delay(200*us)

    @kernel
    def write_output (self, channel, value):

        self.core.break_realtime()

        if value >= 10:
            value = 9.99
        elif value <= -10:
            value = -10.0

        self.zotino0.write_dac(channel, value)
        self.zotino0.load()
        # delay(100*us)

    @kernel
    def proportional_multiply (self, error, Kp):
        temp = error * Kp
        return temp

    @kernel
    def integral_part (self, error, integral_in, Ki):
        temp = integral_in + error
        integrated_out = temp*Ki
        if integrated_out >= 10:
            temp = temp - error
        elif integrated_out <= -10:
            temp = temp - error
        integral_in = temp
        return integral_in, integrated_out

    @kernel
    def derivative_part (self, error, last_error, Kd):
        derivative = error - last_error
        last_error = error
        derivative_out = Kd*derivative
        return last_error, derivative_out

    def get_PID_coeffs(self):
        self.Kp = get_value ("Specify Kp:\n")
        print("Kp = {}".format(self.Kp))
        self.Ki = get_value ("Specify Ki:\n")
        print("Ki = {}".format(self.Ki))
        self.Kd = get_value ("Specify Kd:\n")
        print("Kd = {}".format(self.Kd))
