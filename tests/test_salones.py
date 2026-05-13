def test_salones_publico(client):
    res = client.get('/api/v1/salones')
    assert res.status_code == 200
    body = res.get_json()
    assert isinstance(body['data'], list)
    assert body['total'] >= 1
    s = body['data'][0]
    for k in ('id', 'codigo', 'tipo', 'capacidad', 'disponible_ahora'):
        assert k in s


def test_salon_detail_codigo(client):
    res = client.get('/api/v1/salones/codigo/T-101')
    assert res.status_code == 200
    body = res.get_json()
    assert body['salon']['codigo'] == 'T-101'
    assert 'disponibilidad_semana' in body
    for d in ('lun', 'mar', 'mie', 'jue', 'vie', 'sab'):
        assert d in body['disponibilidad_semana']


def test_salon_detail_404(client):
    res = client.get('/api/v1/salones/codigo/NO-EXISTE')
    assert res.status_code == 404
    assert res.get_json()['code'] == 'NOT_FOUND'
