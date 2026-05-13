from flask import request


def paginate(query, default_per_page=25, max_per_page=100):
    """Pagina una query SQLAlchemy y devuelve (items, meta)."""
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get('per_page', default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = max(1, min(per_page, max_per_page))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
    }
    return pagination.items, meta
