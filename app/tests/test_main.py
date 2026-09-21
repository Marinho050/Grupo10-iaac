from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == ['ok']

def test_predict(test_client):
    input_data = {
        'mean_radius': 18.94,
        'mean_texture': 21.31,
        'mean_perimeter': 123.6,
        'mean_area': 1130.0,
        'mean_smoothness': 0.09009,
        'mean_compactness': 0.1029,
        'mean_concavity': 0.108,
        'mean_concave_points': 0.07951,
        'mean_symmetry': 0.1582,
        'mean_fractal_dimension': 0.05461,
        'radius_error': 0.7888,
        'texture_error': 0.7975,
        'perimeter_error': 5.486,
        'area_error': 96.05,
        'smoothness_error': 0.004444,
        'compactness_error': 0.01652,
        'concavity_error': 0.02269,
        'concave_points_error': 0.0137,
        'symmetry_error': 0.01386,
        'fractal_dimension_error': 0.001698,
        'worst_radius': 24.86,
        'worst_texture': 26.58,
        'worst_perimeter': 165.9,
        'worst_area': 1866.0,
        'worst_smoothness': 0.1193,
        'worst_compactness': 0.2336,
        'worst_concavity': 0.2687,
        'worst_concave_points': 0.1789,
        'worst_symmetry': 0.2551,
        'worst_fractal_dimension': 0.06589
        }

    response = test_client.post('/predict', json=input_data)

    assert response.status_code == 200
    assert response.json()['predict'] == 0
    assert isinstance(response.json()["predict_prob"], float)