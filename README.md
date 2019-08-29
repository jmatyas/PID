# PID
Proportional-Derivative-Integral controller for laser stabilization at HU Berlin.

23.08.2019

    Successful laser locking with this PID. Coefficients used for locking : Kp = 0.2, Ki = 0.2, Kd = 0.0.
    10 dB attenuator used just after DAC.
    Laser currnent controller used in locking experiment: the one above, HU rev 7.2017

26.08.2019
    The sharpest peak were achieved with coefficients: Kp=0.1, Ki =0.05. Adding derivative part only broadened thee peak.


28.08
    Kp 0.0025
    Ki 0.001

29.08
    Network analyzer used to determine PID's transfer function. Every part of PID controller behaves as expected when given input across wide range of frequency.
    The experiment is being conducted wiith parameteres as follows:
        sweep range: 50 Hz - 10 kHz
        amp - 10 dBm
        input: only A - 20 dB attenuator was used for calibration, otherwise NA's input was overloaded

    Following coefficients should be set to gather data:
        Kp  1
        Ki  0
        Kd  0

        Kp  0
        Ki  1
        Kd  0

        Kp  0
        Ki  0
        Kd  1

        Setting, wich was the best for locking laser:
        Kp  0.0025
        Ki  0.001
        Kd  0

        Kp  [0.025  0.25    2.5     10]
        Ki  [0.01   0.1     1       10]
        Kd  [0.01   0.1     1       10]