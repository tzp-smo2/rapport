import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit

def detect_seuils_smo2_sep(x, y):
    # Lissage Savitzky-Golay
    y_lisse = savgol_filter(y, window_length=11, polyorder=2)

    # Seuil 1 = modèle linéaire par morceaux
    def piecewise_linear(x, x0, y0, k1, k2):
        return np.where(x < x0, k1*(x - x0) + y0, k2*(x - x0) + y0)

    p0 = [np.median(x), np.median(y_lisse), -0.1, -1.0]
    params1, _ = curve_fit(piecewise_linear, x, y_lisse, p0)
    x0, y0, k1, k2 = params1  # Seuil 1

    # Seuil 2 = pente redevenant faible après S1
    dy_dt = np.gradient(y_lisse, x)
    idx_post = np.where(x > x0)[0]
    idx_s2 = idx_post[np.argmax(dy_dt[idx_post] > -0.005)]
    x0_2 = x[idx_s2]
    y0_2 = y_lisse[idx_s2]

    return x0, y0, x0_2, y0_2, y_lisse, params1
