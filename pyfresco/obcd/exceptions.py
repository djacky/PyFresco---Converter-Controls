from pyfresco.obcd import constants as cn


class Check:

    @staticmethod
    def check_ib_pars(user_pars, print_callback):

        limits = cn.limits_ib
        limits_int = ['n_integrators', 'n_r', 'n_s', 'n_t', 'n_ilc', 'n_q']
        web_info = 'See https://acc-py.web.cern.ch/gitlab-mono/ccs/fgc/docs/pyfresco/' \
            ' for more information.'

        for key in limits:
            if (isinstance(vars(user_pars)[key], float) or
                    isinstance(vars(user_pars)[key], int)) and not \
                    isinstance(vars(user_pars)[key], bool):
                if vars(user_pars)[key] < limits[key][0] or \
                        vars(user_pars)[key] > limits[key][1]:
                    raise Exception(f'Parameter {key} out of limits. {web_info}')
            elif isinstance(vars(user_pars)[key], str):
                if vars(user_pars)[key] not in limits[key]:
                    raise Exception(f'Parameter {key} not the correct string. {web_info}')
            elif isinstance(vars(user_pars)[key], bool):
                if vars(user_pars)[key] not in limits[key]:
                    raise Exception(f'Parameter {key} not the correct string. {web_info}')
            else:
                raise Exception(f'{key} is not a valid character. {web_info}')

        for key in limits_int:
            if isinstance(vars(user_pars)[key], float):
                raise Exception(f'Parameter {key} must be a positive integer.{web_info}')

        print_callback('info', 'All UI parameters within limits. Continuing optimization.')

    @staticmethod
    def check_v_pars(user_pars, print_callback):

        limits = cn.limits_v
        web_info = 'See https://acc-py.web.cern.ch/gitlab-mono/ccs/fgc/docs/pyfresco/' \
            ' for more information.'

        for key in limits:
            if isinstance(vars(user_pars)[key], float) or \
                    isinstance(vars(user_pars)[key], int):
                if vars(user_pars)[key] < limits[key][0] or \
                        vars(user_pars)[key] > limits[key][1]:
                    raise Exception(f'Parameter {key} out of limits. {web_info}')
            elif isinstance(vars(user_pars)[key], str):
                if vars(user_pars)[key] not in limits[key]:
                    raise Exception(f'Parameter {key} not the correct string. {web_info}')
            elif isinstance(vars(user_pars)[key], bool):
                if vars(user_pars)[key] not in limits[key]:
                    raise Exception(f'Parameter {key} not the correct string. {web_info}')
            else:
                raise Exception(f'{key} is not a valid character. {web_info}')

        print_callback('info', 'All UI parameters within limits. Continuing optimization.')

    @staticmethod
    def prop_ib_model(user_pars, fgc_prop, print_callback):

        props_0_not_allowed = ['LOAD.OHMS_MAG', 'LOAD.HENRYS', 'VS.SIM.BANDWIDTH',
                            'VS.SIM.Z', 'LOAD.OHMS_PAR', 'LOAD.GAUSS_PER_AMP']

        for props in props_0_not_allowed:
            if fgc_prop[props] <= 0 and user_pars.control_mode == 'B':
                raise Exception(f'Cannot have {props} <= 0 in field control.')
            elif fgc_prop[props] <= 0:
                raise Exception(f'Cannot have {props} <= 0.')

        if fgc_prop['VS.ACTUATION'] == 'FIRING_REF':
            print_callback('warning',
                'VS.ACTUATION is set to FIRING_REF. Ensure that '
                'VS.FIRING.DELAY is set correctly.')

        int_delay = 'REG.{}.INTERNAL.PURE_DELAY_PERIODS'.format(user_pars.control_mode)
        if fgc_prop[int_delay] > 0:
            print_callback('warning',
                f'{int_delay} is > 0. This value will be used as the total'
                ' pure delay in the open loop.')

    @staticmethod
    def prop_v_model(fgc_prop, print_callback):

        props_0_not_allowed = ['LOAD.OHMS_MAG', 'LOAD.HENRYS', 'LOAD.OHMS_PAR',
                'VS.FILTER.FARADS1', 'VS.FILTER.FARADS2', 'VS.FILTER.OHMS', 'VS.FILTER.HENRYS']

        for props in props_0_not_allowed:
            if fgc_prop[props] <= 0:
                raise Exception(f'Cannot have {props} <= 0.')

        if fgc_prop['VS.ACTUATION'] == 'FIRING_REF':
            print_callback('warning',
                'VS.ACTUATION is set to FIRING_REF. Ensure that'
                ' VS.FIRING.DELAY is set correctly.')

        int_delay = 'REG.I.INTERNAL.PURE_DELAY_PERIODS'
        if fgc_prop[int_delay] > 0:
            print_callback('warning',
            f'{int_delay} is > 0. This value will be used as the total'
            'pure delay in the open loop.')