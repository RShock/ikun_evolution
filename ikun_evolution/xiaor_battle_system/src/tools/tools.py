from lagom import Container


def get_num(s: str) -> int:
    num = ''.join([x for x in s if x.isdigit()])
    return 0 if num == '' else int(num)


# lagom的container怎么不是单例模式？？
_container = None


def get_container():
    global _container
    if _container is None:
        _container = Container()
    return _container
