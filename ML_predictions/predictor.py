import numpy as np
import pickle


class Predictor:
    def __init__(self, path):
        self.model = pickle.load(open(path, 'rb'))


    def predict(self, X=None):
        # Make predictions
        y_pred = self.model.predict(X)

        return y_pred
            
