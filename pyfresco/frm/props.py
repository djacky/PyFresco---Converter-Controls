

class UiParams:
    """
    A class which contains the default values to be used for the FRM UI.
    """
    def __init__(self):
        self.reg_mode = None
        self.ref_mode = None
        self.meas_mode = None
        self.period_iters = None
        self.amplitude_pp = None
        self.k_order = None
        self.num_sequences = None
        self.num_freq = None


    @staticmethod
    def get_default_prbs():
        """
        :return: Object which contains the UI paramater default values
                 (for PRBS measurememt).
        :rtype: class
        """
        default = UiParams()
        props_prbs = {'reg_mode': 'V', 'ref_mode': 'V_REF', 'meas_mode': 'I_MEAS',
        'period_iters': int(1), 'k_order': int(12), 'amplitude_pp': 0.5,  'num_sequences': int(12)}
        for prop in props_prbs:
            setattr(default, prop, props_prbs[prop])
        return default

    @staticmethod
    def get_default_sine():
        """
        :return: Object which contains the UI paramater default values
                 (for Sine-Fit measurememt).
        :rtype: class
        """
        default = UiParams()
        props_sine = {'reg_mode': 'V', 'ref_mode': 'V_REF', 'meas_mode': 'I_MEAS',
                    'num_freq': int(200)}
        for prop in props_sine:
            setattr(default, prop, props_sine[prop])
        return default