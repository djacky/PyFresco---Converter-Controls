from pyfresco.frm import constants as cn


class Check:

    @staticmethod
    def check_prbs_pars(user_pars):

        limits = cn.limits_prbs
        web_info = 'See https://acc-py.web.cern.ch/gitlab-mono/ccs/fgc/docs/pyfresco/' \
            ' for more information.'

        for key in limits:
            if isinstance(vars(user_pars)[key], float) or \
                    isinstance(vars(user_pars)[key], int):
                if vars(user_pars)[key] < limits[key][0] or \
                        vars(user_pars)[key] > limits[key][1]:
                    raise Exception(f'Parameter {key} out of limits. {web_info}')
            elif isinstance(vars(user_pars)[key], str):
                pass
            else:
                raise Exception(f'{key} is not a valid character. {web_info}')

        print('All UI parameters within limits. Continuing measurements.')

    @staticmethod
    def check_sine_pars(user_pars):

        limits = cn.limits_sine
        web_info = 'See https://acc-py.web.cern.ch/gitlab-mono/ccs/fgc/docs/pyfresco/' \
            ' for more information.'

        for key in limits:
            if isinstance(vars(user_pars)[key], float) or \
                    isinstance(vars(user_pars)[key], int):
                if vars(user_pars)[key] < limits[key][0] or \
                        vars(user_pars)[key] > limits[key][1]:
                    raise Exception(f'Parameter {key} out of limits. {web_info}')
            elif isinstance(vars(user_pars)[key], str):
                pass
            else:
                raise Exception(f'{key} is not a valid character. {web_info}')

        print('All UI parameters within limits. Continuing measurements.')
