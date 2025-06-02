'''
An infinite mock object, where you can follow any chain of attributes or items
within reason, even invoking methods, without knowing anything about the
underlying object. This allows loading otherwise unloadable modules.
'''

from typing import Any

_no_proxy = frozenset((
    'in_traceback', '_path_', '__path_',
    '__getattr__', '__setattr__', '__getitem__',
    '__setitem__', '__iter__', '__len__', '__int__',
    '__float__', '__str__', '__call__', '__repr__',
    '_path_', '_in_traceback_', '_hou_',
))

class InfiniteMock:
    """
    A mock class that allows infinite access to attributes.
    This class is used to access attributes the UI and qt attributes of
    the hou module, allowing modules which reference them to load
    successfully.
    """
    _in_traceback_: bool = False
    _path_: str
    _hou_: Any
    def __init__(self, hou: Any, path: str ):
        self._hou_ = hou
        self._path_ = path
    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute from the mock object.
        Args:
            name (str): The name of the attribute to get.
        Returns:
            Any: The attribute from the mock object.
        """
        if name in _no_proxy:
            return super().__getattribute__(name)
        path = f'{self._path_}.{name}'
        match name:
            case 'colorFromName':
                def colorFromName(*args, **kwargs):
                    print(f'colorFromName({args}, {kwargs})')
                    return self._hou_.Color()
                return colorFromName
            case '__mro_entries__':
                def mro_entries(cls, *args, **kwargs):
                    return ()
                return mro_entries
            case 'this':
                if self._in_traceback_:
                    return path
                try:
                    raise AttributeError(
                        "hou.ui.this is not available."
                    )
                except AttributeError as e:
                    self.in_traceback = True
                    traceback = e.__traceback__
                    while traceback:
                        print("{}: {}".format(traceback.tb_frame.f_code.co_filename,
                                              traceback.tb_lineno))
                        traceback = traceback.tb_next
                    return InfiniteMock(self._hou_, path)
        return InfiniteMock(self._hou_, path)

    def __setattr__(self, name: str, value: Any):
        """
        Set an attribute in the mock object.
        Args:
            name (str): The name of the attribute to set.
            value (Any): The value to set the attribute to.
        """
        if name in _no_proxy:
            return super().__setattr__(name, value)

    def __getitem__(self, key: str) -> 'InfiniteMock':
        """
        Get an item from the mock object.
        Args:
            key (str): The key of the item to get.
        Returns:
            InfiniteMock: A mock object for an unavailable item in the hou module.
        """
        return InfiniteMock(self._hou_, f'{self._path_}[{key}]')

    def __setitem__(self, key: str, value: Any):
        """
        Set an item in the mock object.
        Args:
            key (str): The key of the item to set.
            value (Any): The value to set the item to.
        """
        pass

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        """
        Get the length of the mock object.
        Returns:
            int: The length of the object, which is always 0.
        """
        return 0

    def __int__(self) -> int:
        """
        Convert the value to an integer.
        Returns:
            int: Always returns 0.
        """
        return 10

    def __index__(self) -> int:
        """
        Convert the mock object to an index.
        Returns:
            int: Always returns 10 (ro avoid division by zero).
        """
        return 10

    def __bool__(self) -> bool:
        """
        Convert the mock object to an index.
        Returns:
            bool: Always returns False.
        """
        return False

    def __float__(self) -> float:
        """
        Convert the mock object to a float.
        Returns:
            float: Always returns 10.0 (to avoid division by zero).
        """
        return 10.0

    def __str__(self) -> str:
        """
        Convert the mock object to a string.
        Returns:
            str: Always returns an empty string.
        """
        return f'proxy({self._path_})'

    def __repr__(self) -> str:
        """
        Get a string representation of the mock object.
        Returns:
            str: A string representation of the mock object.
        """
        return f'InfiniteMock({self._path_})'

    def __call__(self, *args, **kwargs) -> 'InfiniteMock':
        """
        Call and return myself.
        """
        return InfiniteMock(self._hou_, f'{self._path_}()')
