from fastapi.testclient import TestClient

from app.backend.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_regions() -> None:
    response = client.get('/api/v1/regions')
    assert response.status_code == 200
    regions = response.json()['regions']
    assert any(item['code'] == 'us-east-1' for item in regions)


def test_generate_png() -> None:
    response = client.post(
        '/api/v1/diagram.png',
        json={
            'customer_name': 'Acme',
            'region': 'us-east-1',
            'production_server_count': 2,
            'availability_zone_count': 2,
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert len(response.content) > 0


def test_reject_unknown_region() -> None:
    response = client.post(
        '/api/v1/diagram.png',
        json={
            'customer_name': 'Acme',
            'region': 'bad-region',
            'production_server_count': 2,
            'availability_zone_count': 2,
            'non_production_server_count': 1,
        },
    )
    assert response.status_code == 400
