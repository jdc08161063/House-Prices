import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from sklearn.base import BaseEstimator, RegressorMixin

def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

# CV
def evaludate_model(model, x, y):
    print('Cross_validation..')
    n_splits_val = 10
    kf = KFold(n_splits=n_splits_val, shuffle=False)
    idx = 0
    rmse_buf = np.empty(n_splits_val)
    for train, test in kf.split(x):
        model.fit(x.iloc[train], y.iloc[train])
        y_cv = model.predict(x.iloc[test])
        rmse_buf[idx] = rmse(y.iloc[test], y_cv)
        # print('Interation #' + str(idx) + ': RMSE = %.5f' % rmse_buf[idx])
        idx += 1

    mean_rmse = np.mean(rmse_buf)
    print('   Mean RMSE = %.5f' % mean_rmse + ' +/- %.5f' % np.std(rmse_buf))

    return mean_rmse

def evaludate_submodels(models, x, y):
    print('Cross_validation..')
    n_splits_val = 10
    kf = KFold(n_splits=n_splits_val, shuffle=False)
    for m_i, model in enumerate(models.regressors):
        rmse_buf = np.empty(n_splits_val)
        idx = 0
        for train, test in kf.split(x):
            model.fit(x.iloc[train], y.iloc[train])
            y_cv = model.predict(x.iloc[test])
            rmse_buf[idx] = rmse(y.iloc[test], y_cv)
            # print('Interation #' + str(idx) + ': RMSE = %.5f' % rmse_buf[idx])
            idx += 1

        mean_rmse = np.mean(rmse_buf)
        print('Model #' + str(m_i) + ': mean RMSE = %.5f' % mean_rmse + \
              ' +/- %.5f' % np.std(rmse_buf))


class AverageEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, regressors=None):
        self.regressors = regressors

    def fit(self, X, y):
        for regressor in self.regressors:
            regressor.fit(X, y)

    def predict(self, X):
        self.predictions_ = list()
        for regressor in self.regressors:
            self.predictions_.append(regressor.predict(X).ravel())

        # res = 0.45*self.predictions_[1] + 0.25*self.predictions_[0] + 0.30*self.predictions_[2]
        res = np.mean(self.predictions_, axis=0)

        return res


class StackingEnsemble(object):
    def __init__(self, n_splits, stacker, base_models):
        self.n_splits = n_splits
        self.stacker = stacker
        self.base_models = base_models

    def fit_predict(self, X, y, T):
        X = np.array(X)
        y = np.array(y)
        T = np.array(T)
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)

        S_train = np.zeros((X.shape[0], len(self.base_models)))
        S_test = np.zeros((T.shape[0], len(self.base_models)))
        for i, clf in enumerate(self.base_models):
            S_test_i = np.zeros((T.shape[0], kf.get_n_splits()))
            for j, (train_idx, test_idx) in enumerate(kf.split(X)):
                X_train = X[train_idx]
                y_train = y[train_idx]
                X_holdout = X[test_idx]
                # y_holdout = y[test_idx]
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_holdout).ravel()
                S_train[test_idx, i] = y_pred
                S_test_i[:, j] = clf.predict(T).ravel()
            S_test[:, i] = S_test_i.mean(1)
        self.stacker.fit(S_train, y)
        y_pred = self.stacker.predict(S_test)[:]
        return y_pred
