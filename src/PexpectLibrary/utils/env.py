import os


def get_env_flag(env, default=False):
    return os.environ.get(env, "on" if default else "off").lower() == "on"


def get_int_env(env, default=None):
    _value = os.environ.get(env)
    try:
        _value = int(_value)
    except  Exception:
        _value = default
    return _value
