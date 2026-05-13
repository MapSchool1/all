def test_horario_estudiante_con_conflicto(client, estudiante_token):
    """El seed crea un horario con dos bloques solapados en mié 11:00."""
    listing = client.get('/api/v1/horarios',
                         headers={'Authorization': f'Bearer {estudiante_token}'})
    assert listing.status_code == 200
    horarios = listing.get_json()['data']
    assert len(horarios) >= 1
    h_id = horarios[0]['id']
    assert horarios[0]['tiene_conflictos'] is True

    detail = client.get(f'/api/v1/horarios/{h_id}',
                        headers={'Authorization': f'Bearer {estudiante_token}'})
    assert detail.status_code == 200
    body = detail.get_json()
    bloques_conflicto = [b for b in body['bloques'] if b['conflicto']]
    assert len(bloques_conflicto) == 2
    for b in bloques_conflicto:
        assert b['dia'] == 'mie'
        assert b['hora_inicio'] == '11:00'


def test_dashboard_admin(client, admin_token):
    res = client.get('/api/v1/stats/dashboard',
                     headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    body = res.get_json()
    for k in ('estudiantes_activos', 'horarios_publicados',
              'conflictos_abiertos', 'asistencia_promedio',
              'tramites_pendientes', 'nuevos_hoy'):
        assert k in body
    # El conflicto creado en el seed debe contar
    assert body['conflictos_abiertos']['total'] >= 1
