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
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
            'footer_text': 'Test footer text',
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/png'
    assert len(response.content) > 0


def test_generate_jpeg() -> None:
    response = client.post(
        '/api/v1/diagram.jpg',
        json={
            'customer_name': 'Acme',
            'region': 'us-east-1',
            'production_server_count': 2,
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
            'footer_text': 'Test footer text',
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert len(response.content) > 0


def test_generate_pdf() -> None:
    response = client.post(
        '/api/v1/diagram.pdf',
        json={
            'customer_name': 'Acme',
            'region': 'us-east-1',
            'production_server_count': 2,
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
            'footer_text': 'Test footer text',
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert len(response.content) > 0


def test_generate_drawio() -> None:
    response = client.post(
        '/api/v1/diagram.drawio',
        json={
            'customer_name': 'Acme',
            'region': 'us-east-1',
            'production_server_count': 2,
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
            'footer_text': 'Test footer text',
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/xml'
    assert len(response.content) > 0
    assert b'<mxfile' in response.content


def test_generate_excalidraw() -> None:
    response = client.post(
        '/api/v1/diagram.excalidraw',
        json={
            'customer_name': 'Acme',
            'region': 'us-east-1',
            'production_server_count': 2,
            'non_production_server_count': 1,
            'include_rds': True,
            'include_fsx': True,
            'footer_text': 'Test footer text',
        },
    )
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'
    import json
    data = json.loads(response.content)
    assert data['type'] == 'excalidraw'
    assert len(data['elements']) > 0


def test_reject_unknown_region() -> None:
    response = client.post(
        '/api/v1/diagram.png',
        json={
            'customer_name': 'Acme',
            'region': 'bad-region',
            'production_server_count': 2,
            'non_production_server_count': 1,
        },
    )
    assert response.status_code == 400
