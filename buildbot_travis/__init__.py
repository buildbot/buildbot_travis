def TravisConfigurator(*args, **kw):
    from .configurator import TravisConfigurator as tc
    return tc(*args, **kw)

__all__ = ['TravisConfigurator', 'ep']
