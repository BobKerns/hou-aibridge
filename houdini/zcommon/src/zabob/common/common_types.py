'''
Type definitions common to houdini and python submodules
'''

from typing import TypeAlias

# There is a better version available in 3.12 with the type keyword.
# See zabob.core.core_types for the new version.

JsonAtomicNonNull: TypeAlias = str|int|float|bool
JsonAtomic: TypeAlias = JsonAtomicNonNull|None
JsonArray: TypeAlias = list['JsonData']
JsonObject: TypeAlias = dict[str, 'JsonData']
JsonDataNonNull: TypeAlias = JsonArray|JsonObject|JsonAtomicNonNull
JsonData: TypeAlias = JsonDataNonNull|None
