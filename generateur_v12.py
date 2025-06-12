import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

def detect_seuils_smo2_physio(x, y):
    # Lissage
    y_lisse = savgol_filter(y, window_length=11, polyorder=2)

    # Pente
    dy_dt = np.gradient(y_lisse, x)

    # Seuil 1 : première pente forte négative
    idx_s1 = np.argmax(dy_dt < -0.03)
    x0 = x[idx_s1]
    y0 = y_lisse[idx_s1]

    # Seuil 2 : pente qui devient faible
    idx_post = np.where(x > x0)[0]
    idx_s2 = idx_post[np.argmax(dy_dt[idx_post] > -0.005)]
    x0_2 = x[idx_s2]
    y0_2 = y_lisse[idx_s2]

    return x0, y0, x0_2, y0_2, y_lisse
