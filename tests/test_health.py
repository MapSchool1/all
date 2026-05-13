def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    body = res.get_json()
    assert body['status'] == 'ok'
    assert body['db'] == 'ok'
    assert 'version' in body
