from .compat import basestring


def _split_params_and_files(params_):
    params = {}
    files = {}
    for k, v in params_.items():
        if hasattr(v, 'read') and callable(v.read):
            files[k] = v
        elif isinstance(v, basestring):
            params[k] = v
        elif isinstance(v, bool):
            params[k] = 'true' if v else 'false'
    return params, files
