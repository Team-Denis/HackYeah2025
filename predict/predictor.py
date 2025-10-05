import numpy as np
import pickle
from typing import Any, Dict
import datetime


class Predictor:

    """A simple predictor class that loads a pre-trained KNN model and makes predictions with confidence."""

    def __init__(self, path: str) -> None:
        # Load the model from disk
        self.model: Any = pickle.load(open(path, 'rb'))

    def transform(self, incident: Dict[str, Any]) -> np.ndarray:
        X = []

        dt_obj = datetime.datetime.fromisoformat(incident['created_at'])
        hour = dt_obj.hour
        day_of_week = dt_obj.weekday()
        is_rush_hour = int(hour in [7, 8, 9, 16, 17, 18])

        status = 1 if incident['status'] == 'RESOLVED' else 0

        X.append([
            incident['location_id'],
            incident['type_id'],
            incident['trust_score'],
            status,
            hour,
            day_of_week,
            is_rush_hour
        ])

        return np.array(X)

    def predict(self, X: np.ndarray) -> float:
        # Simple prediction
        return self.model.predict(X)[0]

    def interpret(self, X: np.ndarray) -> float:
        cluster = self.model.predict(X)[0]
        center = self.model.cluster_centers_[cluster]
        dist = np.linalg.norm(X[0] - center)
        confidence = max(0, 100 - dist*10)
        return confidence / 100


if __name__ == "__main__":

    predictor = Predictor("predict/knn_model.pkl")

    # ex
    incident = {
        "location_id": 1_5,
        "type_id": 3,
        "trust_score": 0.8,
        "status": "DELAYED",
        "created_at": "2025-10-05T08:30:00",
        "avg_delay": 15
    }

    X = predictor.transform(incident)
    prediction = predictor.predict(X)
    confidence = predictor.interpret(X)
