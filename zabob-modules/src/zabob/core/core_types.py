'''
Utility types (requires python 3.12+)
'''

type JsonAtomicNonNull = str|int|float|bool
type JsonAtomic = JsonAtomicNonNull|None
type JsonArray = list['JsonData']
type JsonObject = dict[str, JsonData]
type JsonDataNonNull = JsonArray|JsonObject|JsonAtomicNonNull
type JsonData = JsonDataNonNull|None
