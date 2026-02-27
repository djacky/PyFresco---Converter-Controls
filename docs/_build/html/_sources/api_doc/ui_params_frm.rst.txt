UI Parameters (FRM)
===================
This section contains all of the parameters and keys that PyFresco uses to measure the frequency
response of a power converter system. These parameters are UI inputs that should be stored as class attributes.


FRM Keys
--------
The PRBS and Sine-fit methods both require three main parameters that the user must select: 
Regulation Mode, Input, and Output. The details of these parameters are outline below.
Note that the Sine-fit algorithm does not require other input parameters to obtain a frequency response.

.. _reg_mode_ident:

**Regulation Mode:** 

    :keyword: 
        :code:`reg_mode`

        Desired mode to be in when performing the measurement experiments.

        ``V``: Control system is in open-loop mode. (in the FGC, this is set with REG.MODE V)

        ``I``: RST for the current-loop is enabled (in the FGC, this is set with REG.MODE I)

        ``B``: RST for the field-loop is enabled (in the FGC, this is set with REG.MODE B)

    :Type: 
        ``str``
        
    :Default: 
        ``V``
        
    :Recommended: 
        If the purpose of the measurement is to synthesize an RST and ILC controller, use ``V``.
        For synthesizing controllers for the voltage loop, use ``V``.
        ``I`` or ``B`` are generally used for analysis purposes (i.e., confirming the closed-loop behavior).
        
    :Feasible values: 
        [``I``, ``B``, ``V``]

----

.. _ref_mode:

**Input:**
          
    :keyword: 
        :code:`ref_mode`
    
        The input signal name of the measurement (i.e., signal name from FGC log).

    :Type: 
        ``str``
          
    :Default: 
        ``V_REF``
          
    :Recommended: 
        Not applicable.
          
    :Feasible values: 
        If :ref:`Regulation Mode <reg_mode_ident>` is ``V``:
        [``V_REF``, ``F_REF_LIMITED``, ``V_MEAS``]

        If :ref:`Regulation Mode <reg_mode_ident>` is ``I``:
        [``I_REF_ADV``]

        If :ref:`Regulation Mode <reg_mode_ident>` is ``B``:
        [``B_REF_ADV``]

----

.. _meas_mode:

**Output:**
          
    :keyword: 
        :code:`meas_mode`
    
        The output signal name of the measurement (i.e., signal name from FGC log).

    :Type: 
        ``str``
          
    :Default: 
        ``I_MEAS``
          
    :Recommended: 
        Not applicable.
          
    :Feasible values:
        If :ref:`Regulation Mode <reg_mode_ident>` is ``V``:
        [``V_MEAS``, ``I_CAPA``, ``V_MEAS_REG``, ``I_MEAS``, ``B_MEAS``]

        If :ref:`Regulation Mode <reg_mode_ident>` is ``I``:
        [``I_MEAS_REG``]

        If :ref:`Regulation Mode <reg_mode_ident>` is ``B``:
        [``B_MEAS_REG``]

----

Sine-Fit Keys
~~~~~~~~~~~~~

.. _num_freq:

**Frequency Array:**
          
    :keyword: 
        :code:`num_freq`
    
        Number of frequencies points to measure within the user defined frequencies :math:`[f_{min},f_{max}]`.

    :Type: 
        ``int``
          
    :Default: 
        :math:`200`

    :Recommended: 
        For controller synthesis purposes, values between 150 and 300 should suffice. 

    :Feasible values: 
        :math:`[2, 10^4]`

----

PRBS Keys
~~~~~~~~~

.. _period_iters:

**Period Iters:**
          
    :keyword: 
        :code:`period_iters`
    
        The number of samples in the shortest PRBS step. the 
        highest frequency point in the Bode plot will be :math:`F_s / (2 \times` ``period_iters``:math:`)`
        
        If :ref:`Regulation Mode <reg_mode_ident>` is ``V``, :math:`F_s = (\text{FGC.ITER_PERIOD})^{-1}`.

        If :ref:`Regulation Mode <reg_mode_ident>` is ``I/B``, :math:`F_s` is given in :eq:`Fs`.

    :Type: 
        ``int``
          
    :Default: 
        1
          
    :Recommended: 
        1
          
    :Feasible values: 
        :math:`[1, 10]`

----

.. _amplitude_pp:

**Peak-to-Peak Amplitude:**
          
    :keyword: 
        :code:`amplitude_pp`
    
        The peak-to-peak amplitude of the PRBS step.

    :Type: 
        ``float``
          
    :Default: 
        1
          
    :Recommended: 
        Application dependent. The user should abide by the limits set within the FGC:
        `LIMITS.V.POS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.V.POS>`__ /
        `LIMITS.V.NEG <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.V.NEG>`__ ,
        `LIMITS.I.POS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.I.POS>`__ /
        `LIMITS.I.NEG <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.I.NEG>`__ ,
        `LIMITS.B.POS <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.B.POS>`__ /
        `LIMITS.B.NEG <http://proj-fgc.web.cern.ch/proj-fgc/gendoc/def/PropertyLIMITS.htm#LIMITS.B.NEG>`__ .

    :Feasible values: 
        :math:`(0, 10^6]`

----

.. _num_sequences:

**Num. of Sequences:**
          
    :keyword: 
        :code:`num_sequences`
    
        The number of PRBS periods. One PRBS period has a length of 
        :math:`2^{\text{k_order}} - 1`.

    :Type: 
        ``int``
          
    :Default: 
        15
          
    :Recommended: 
        Application dependent. The value should be selected such that the drift
        is elimiated several periods before the end of the PRBS sequence. In general, 
        any value between 10 and 20 should suffice.
          
    :Feasible values: 
        :math:`[6, 50]`

----

.. _k_order:

**K order:**
          
    :keyword: 
        :code:`k_order`
    
        Indicates the size of a unique word of data in the a PRBS sequence.

    :Type: 
        ``int``
          
    :Default: 
        12
          
    :Recommended: 
        Application dependent. The larger the value, the better the resolution 
        at lower frequencies. However, a larger value will require more PRBS samples 
        (and thus more memory).
          
    :Feasible values: 
        :math:`[8, 20]`