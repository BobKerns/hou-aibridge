'''
An infinite mock object, where you can follow any chain of attributes or items
within reason, even invoking methods, without knowing anything about the
underlying object. This allows loading otherwise unloadable modules.
'''

from typing import Any
from types import ModuleType

_no_mock = frozenset((
    'in_traceback', '_path_', '__path_',
    '__getattr__', '__setattr__', '__getitem__',
    '__setitem__', '__iter__', '__len__', '__int__',
    '__index__', '__bool__',
    '__add__', '__radd__', '__sub__', '__rsub__',
    '__neg__', '__mul__', '__rmul__', '__div__',
    '__rdiv__', '__truediv__', '__rtruediv__',
    '__divmod__', '__rdivmod__', '__floordiv__',
    '__rfloordiv__', '__mod__', '__rmod__',
    '__pow__', '__rpow__', '__lshift__', '__rlshift__',
    '__rshift__', '__rrshift__', '__and__', '__rand__',
    '__or__', '__ror__', '__xor__', '__rxor__',
    '__float__', '__str__', '__call__', '__repr__',
    '_in_traceback_', '_hou_',
    '__name__',
))

class InfiniteMock(ModuleType):
    """
    A mock class that allows infinite access to attributes.
    This class is used to access attributes the UI and qt attributes of
    the hou module, allowing modules which reference them to load
    successfully.
    """
    _in_traceback_: bool = False
    __name__: str
    _hou_: Any
    def __init__(self, hou: Any, path: str ):
        self._hou_ = hou
        self.__name__ = path
    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute from the mock object.
        Args:
            name (str): The name of the attribute to get.
        Returns:
            Any: The attribute from the mock object.
        """
        if name in _no_mock:
            return super().__getattribute__(name)
        path = f'{self.__name__}.{name}'
        match name:
            case 'colorFromName':
                def colorFromName(*args, **kwargs):
                    return self._hou_.Color()
                return colorFromName
            case '__qualname__':
                return self.__name__
            case '__file__'|'__doc__'|'__annotations__':
                return None
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
                        # Print to console for immediate feedback in tuning InfiniteMock
                        # May log to database in the future.
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
        if name in _no_mock:
            return super().__setattr__(name, value)

    def __getitem__(self, key: str) -> 'InfiniteMock':
        """
        Get an item from the mock object.
        Args:
            key (str): The key of the item to get.
        Returns:
            InfiniteMock: A mock object for an unavailable item in the hou module.
        """
        return InfiniteMock(self._hou_, f'{self.__name__}[{key}]')

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
            int: Always returns 10 (to avoid division by zero).
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

    def __add__(self, other: Any):
        '''
        Add the mock object to another value.
        Args:
            other (Any): The other value to add.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        '''
        return other

    def __radd__(self, other: Any):
        """
        Reverse add operation for the mock object.
        Args:
            other (Any): The other value to add.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __sub__(self, other: Any):
        """
        Subtract the mock object from another value.
        Args:
            other (Any): The other value to subtract from.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rsub__(self, other: Any):
        """
        Reverse subtract operation for the mock object.
        Args:
            other (Any): The other value to subtract from.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __neg__(self):
        """
        Negate the mock object.
        Returns:
            InfiniteMock: Returns a new InfiniteMock object with negated name.
        """
        return InfiniteMock(self._hou_, f'-{self.__name__}')

    def __mul__(self, other: Any):
        """
        Multiply the mock object by another value.
        Args:
            other (Any): The other value to multiply with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rmul__(self, other: Any):
        """
        Reverse multiply operation for the mock object.
        Args:
            other (Any): The other value to multiply with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __div__(self, other: Any):
        """
        Divide the mock object by another value.
        Args:
            other (Any): The other value to divide by.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rdiv__(self, other: Any):
        """
        Reverse divide operation for the mock object.
        Args:
            other (Any): The other value to divide by.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __truediv__(self, other: Any):
        """
        True divide the mock object by another value.
        Args:
            other (Any): The other value to divide by.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rtruediv__(self, other: Any):
        """
        Reverse true divide operation for the mock object.
        Args:
            other (Any): The other value to divide by.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __divmod__(self, other: Any):
        """
        Perform divmod operation with the mock object.
        Args:
            other (Any): The other value to perform divmod with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rdivmod__(self, other: Any):
        """
        Reverse divmod operation for the mock object.
        Args:
            other (Any): The other value to perform divmod with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __floordiv__(self, other: Any):
        """
        Perform floor division with the mock object.
        Args:
            other (Any): The other value to perform floor division with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rfloordiv__(self, other: Any):
        """
        Reverse floor division operation for the mock object.
        Args:
            other (Any): The other value to perform floor division with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __mod__(self, other: Any):
        """
        Perform modulo operation with the mock object.
        Args:
            other (Any): The other value to perform modulo with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rmod__(self, other: Any):
        """
        Reverse modulo operation for the mock object.
        Args:
            other (Any): The other value to perform modulo with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __pow__(self, other: Any):
        """
        Raise the mock object to the power of another value.
        Args:
            other (Any): The other value to raise to the power of.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rpow__(self, other: Any):
        """
        Reverse power operation for the mock object.
        Args:
            other (Any): The other value to raise to the power of.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __lshift__(self, other: Any):
        """
        Perform left shift operation with the mock object.
        Args:
            other (Any): The other value to perform left shift with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rlshift__(self, other: Any):
        """
        Reverse left shift operation for the mock object.
        Args:
            other (Any): The other value to perform left shift with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rshift__(self, other: Any):
        """
        Perform right shift operation with the mock object.
        Args:
            other (Any): The other value to perform right shift with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rrshift__(self, other: Any):
        """
        Reverse right shift operation for the mock object.
        Args:
            other (Any): The other value to perform right shift with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __and__(self, other: Any):
        """
        Perform bitwise AND operation with the mock object.
        Args:
            other (Any): The other value to perform bitwise AND with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rand__(self, other: Any):
        """
        Reverse bitwise AND operation for the mock object.
        Args:
            other (Any): The other value to perform bitwise AND with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __or__(self, other: Any):
        """
        Perform bitwise OR operation with the mock object.
        Args:
            other (Any): The other value to perform bitwise OR with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __ror__(self, other: Any):
        """
        Reverse bitwise OR operation for the mock object.
        Args:
            other (Any): The other value to perform bitwise OR with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __xor__(self, other: Any):
        """
        Perform bitwise XOR operation with the mock object.
        Args:
            other (Any): The other value to perform bitwise XOR with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other

    def __rxor__(self, other: Any):
        """
        Reverse bitwise XOR operation for the mock object.
        Args:
            other (Any): The other value to perform bitwise XOR with.
        Returns:
            Any: Returns the other value, effectively ignoring the mock object.
        """
        return other


    def __str__(self) -> str:
        """
        Convert the mock object to a string.
        Returns:
            str: Always returns an empty string.
        """
        return f'proxy({self.__name__})'

    def __repr__(self) -> str:
        """
        Get a string representation of the mock object.
        Returns:
            str: A string representation of the mock object.
        """
        return f'InfiniteMock({self.__name__})'

    def __call__(self, *args, **kwargs) -> 'InfiniteMock':
        """
        Call and return myself.
        """
        return InfiniteMock(self._hou_, f'{self.__name__}()')
