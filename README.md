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
        / x3

        Setting, wich was the best for locking laser:
        Kp  0.0025
        Ki  0.001
        Kd  0
        /x5

        Kp  [0.0025 0.025  0.25    2.5]
        Ki  [0.001  0.01   0.1     1  ]
        Kd  [0      0.01   0.1     1  ]

2.09
    Implementation of PID controller with sampling using only MU units successful (hope so. it seems to work, but id doesnt seemt to improve bandiwdth)
    Starting measuring PID controller - firstly PID from a week before (one which uses sampling to voltages), followed by measuring PID implemented today.
    NA' settings:
        sweep range:    50 - 10000 Hy
        amp:            1 V (without any attenuator)
        input:          only A