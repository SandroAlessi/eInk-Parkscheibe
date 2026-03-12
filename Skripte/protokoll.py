try:
    import utime as _time
except ImportError:
    import time as _time

try:
    import konfiguration as _config
except ImportError:
    _config = None

_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARN": 30,
    "ERROR": 40,
}


def _cfg(name, default):
    if _config is None:
        return default
    return getattr(_config, name, default)


def _now_ms():
    try:
        return _time.ticks_ms()
    except AttributeError:
        try:
            return int(_time.time() * 1000)
        except:
            return 0


def _lvl(value):
    if not value:
        return _LEVELS["DEBUG"]
    return _LEVELS.get(str(value).upper(), _LEVELS["DEBUG"])


def _enabled(level):
    if not _cfg("LOG_ENABLED", True):
        return False
    threshold = _lvl(_cfg("LOG_LEVEL", "DEBUG"))
    return _lvl(level) >= threshold


def log(level, tag, msg, *args):
    lvl_txt = str(level).upper()
    if not _enabled(lvl_txt):
        return
    if args:
        try:
            msg = msg % args
        except:
            msg = str(msg)
    print("[%s][%010d][%s] %s" % (lvl_txt, _now_ms(), tag, msg))


def debug(tag, msg, *args):
    log("DEBUG", tag, msg, *args)


def info(tag, msg, *args):
    log("INFO", tag, msg, *args)


def warn(tag, msg, *args):
    log("WARN", tag, msg, *args)


def error(tag, msg, *args):
    log("ERROR", tag, msg, *args)


def exception(tag, msg, exc=None):
    error(tag, msg)
    if exc is not None:
        error(tag, "Exception: %s", exc)
