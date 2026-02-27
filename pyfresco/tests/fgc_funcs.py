import pyfgc
import pyfresco.obcd as cd


def frm_prbs_vals(device):
    amp_pp = float(pyfgc.get(device, 'REF.PRBS.AMPLITUDE_PP').value)
    period_iters = int(pyfgc.get(device, 'REF.PRBS.PERIOD_ITERS').value)
    num_seq = int(pyfgc.get(device, 'REF.PRBS.NUM_SEQUENCES').value)
    k = int(pyfgc.get(device, 'REF.PRBS.K').value)
    A = {'device': device, 'amp_pp': amp_pp, 'period_iters': period_iters,
        'num_seq': num_seq, 'k': k}

    import midas
    URL = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=11588:53399'
    logs = midas.fetch(URL)
    df_prbs = logs[0].to_dataframe()

    return A, df_prbs


def obcd_model_vals(device):
    user_pars_ib = cd.get_default_i(device)
    fgc_ib = cd.FgcProperties.from_fgc_ib(device)
    user_pars_v = cd.get_default_v(device)
    fgc_v = cd.FgcProperties.from_fgc_v(device)

    A = {'user_pars_ib': user_pars_ib, 'fgc_ib': fgc_ib, 'user_pars_v': user_pars_v,
    'fgc_v': fgc_v}
    return A


def obcd_data_vals(device, mode='I'):
    amp_pp = float(pyfgc.get(device, 'REF.PRBS.AMPLITUDE_PP').value)
    period_iters = int(pyfgc.get(device, 'REF.PRBS.PERIOD_ITERS').value)
    num_seq = int(pyfgc.get(device, 'REF.PRBS.NUM_SEQUENCES').value)
    k = int(pyfgc.get(device, 'REF.PRBS.K').value)
    prbs_pars = {'device': device, 'amp_pp': amp_pp, 'period_iters': period_iters,
        'num_seq': num_seq, 'k': k}

    import midas
    if mode == 'I':
        user_pars_ib = cd.get_default_i(device)
        fgc_ib = cd.FgcProperties.from_fgc_ib(device)
        A = {'user_pars_ib': user_pars_ib, 'fgc_ib': fgc_ib}
        # For current/field control
        # URL = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=8717:48241'
        URL = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=11588:53399'
        logs = midas.fetch(URL)
        df_ib_time = logs[0].to_dataframe()
        df = {'df_ib_time': df_ib_time}
        return prbs_pars, A, df
    elif mode == 'V':
        user_pars_v = cd.get_default_v(device)
        fgc_v = cd.FgcProperties.from_fgc_v(device)
        # For voltage control
        URL = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=8199:47160?history=8199:47161'
        logs = midas.fetch(URL)
        df_vreg = logs[1].to_dataframe()
        df_imeas1 = logs[0].to_dataframe()

        # For DC gain
        URL = 'https://beraymon-preprod.cern.ch/powerspy/chart/?history=8194:47153'
        logs = midas.fetch(URL)
        df_dcgain = logs[0].to_dataframe()
        A = {'user_pars_v': user_pars_v, 'fgc_v': fgc_v}

        df = {'df_vreg': df_vreg, 'df_imeas1': df_imeas1,
            'df_dcgain': df_dcgain}

        return prbs_pars, A, df