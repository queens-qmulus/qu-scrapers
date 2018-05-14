def add_default_fields(data):
    if not data.get('updated'):
        data['updated'] = data['published']

    return data