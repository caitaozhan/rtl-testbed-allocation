import numpy as np
from sklearn.linear_model import LinearRegression


def test():
    X = np.array([[1], [2], [3]])
    y = np.array([3, 5, 7])

    reg = LinearRegression().fit(X, y)

    print(reg.score(X, y))
    print(reg.coef_)
    print(reg.intercept_)
    print(reg.predict(np.array([[4], [5]])))


class Data:
    X = np.array([[40], [45], [50], [55], [60], [65]])   # usrp
    y = np.array([ 14,   20,   30,   33,   41,   44])     # hackrf
    # RX           -45   -41   -35   -29   -24   -20

    X2 = np.array([[25], [30], [35], [40], [45], [50], [55], [60], [65]])
    y2  = np.array([4,    10,   14,   18,   22,   26,   31,   39,   44])
    # RX           -47   -43   -40   -37    -32   -29   -24   -19   -15

    def __init__(self):
        self.reg = LinearRegression().fit(Data.X2, Data.y2)
        print('score', self.reg.score(Data.X2, Data.y2))
        print('coef ', self.reg.coef_)
        print('intercept', self.reg.intercept_)
        print('prediction', self.reg.predict(np.array([[20], [21], [22]])))        
        print('prediction', self.reg.predict(np.array([[69], [70], [71]])))        


if __name__ == '__main__':
    d = Data()
