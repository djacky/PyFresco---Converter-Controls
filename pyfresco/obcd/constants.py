# Statistical parameters used to determine frequency grid (for model-driven control)
epsilon, beta = 0.1, 0.1

# Optimization tolerances
bis_tol, LMI_tol = 1e-5, 1e-3

# Maximim allowable gamma for Hinf control
g_max = 10

# Gamma value which is used to determine infeasibility
g_thresh = 100

# Number of sig. digits for showing optimal gamma
g_digits = 5

# Limits for quality of optimal solutions
hinf_qual = [1.3, 1.8]
h2_qual = 0.15
h1_qual = 0.15

# Max number of coefficients on RST
max_rst_coeff = 16

# Max order of L-filter
max_l_order = 12

# Max order of Q-filter
max_q_order = 12

# RST order vector for initial stabilizing design
init_rst_vec = [6, 8, 10, 12, 16]

# Unicode characters for printing results
uint, usqrt, umag = u'\u222B', u'\u221a', u'\u2016'
upi, uomega, uinf = u'\U0001D70B', u'\u03C9', u'\u221e'
usquare, usubr, usubs = u'\u00B2', u'\u1D63', u'\u209B'
ug, uginf, ug2, ug1 = u'\u03B3', u'\u03B3_inf', u'\u03B3\u2082', u'\u03B3\u2081'
ugq, ugilc = u'\u03B3_q', u'\u03B3\u2097'

dl = 1e-4
limits_ib = {'des_bw': [dl, 10**6], 'des_z': [dl, 1], 'des_mm': [dl, 1 - dl],
'n_integrators': [1, 3], 'ref_delay': [0, 10], 'opt_method': ['Hinf', 'H2', 'H1'],
'n_r': [4, max_rst_coeff], 'n_s': [4, max_rst_coeff], 'n_t': [4, max_rst_coeff],
    'n_ilc': [2, max_l_order], 'n_q': [2, max_q_order], 'q_bw': [dl, 10**6],
    'control_mode': ['I', 'B'], 'test_select': [True, False], 'ilc_only': [True, False],
             'debug': [True, False]}

limits_v = {'damp_bw': [dl, 10**6], 'damp_z': [dl, 1], 'volt_mm': [dl, 1 - dl],
'opt_method': ['Hinf', 'H2'], 'volt_bw': [dl, 10**6], 'volt_z': [dl, 1],
'ref_delay': [0, 10], 'control_mode': 'V'}