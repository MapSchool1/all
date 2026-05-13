def test_login_ok(client):
    res = client.post('/auth/login', json={
        'email': 'admin@test.mx', 'password': 'Admin1234!',
    })
    assert res.status_code == 200
    body = res.get_json()
    assert 'access_token' in body
    assert 'refresh_token' in body
    assert body['user']['email'] == 'admin@test.mx'
    assert body['user']['rol'] == 'admin'


def test_login_credenciales_invalidas(client):
    res = client.post('/auth/login', json={
        'email': 'admin@test.mx', 'password': 'wrong',
    })
    assert res.status_code == 401
    assert res.get_json()['code'] == 'INVALID_CREDENTIALS'


def test_login_email_inexistente(client):
    res = client.post('/auth/login', json={
        'email': 'nope@test.mx', 'password': 'whatever',
    })
    assert res.status_code == 401


def test_login_campos_faltantes(client):
    res = client.post('/auth/login', json={'email': 'admin@test.mx'})
    assert res.status_code == 422


def test_me_requires_auth(client):
    res = client.get('/auth/me')
    assert res.status_code == 401


def test_me_ok(client, admin_token):
    res = client.get('/auth/me',
                     headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    assert res.get_json()['user']['rol'] == 'admin'


def test_estudiante_no_puede_listar_usuarios(client, estudiante_token):
    res = client.get('/api/v1/users',
                     headers={'Authorization': f'Bearer {estudiante_token}'})
    assert res.status_code == 403


def test_admin_puede_listar_usuarios(client, admin_token):
    res = client.get('/api/v1/users',
                     headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    body = res.get_json()
    assert 'data' in body
    assert body['total'] >= 2  # admin + estudiante del seed


def test_refresh_token(client):
    login = client.post('/auth/login', json={
        'email': 'admin@test.mx', 'password': 'Admin1234!',
    }).get_json()
    refresh = login['refresh_token']
    res = client.post('/auth/refresh',
                      headers={'Authorization': f'Bearer {refresh}'})
    assert res.status_code == 200
    new = res.get_json()
    assert 'access_token' in new
    assert new['access_token'] != login['access_token']
