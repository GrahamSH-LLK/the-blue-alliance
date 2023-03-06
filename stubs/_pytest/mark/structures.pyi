import collections.abc
import typing
from .._code import getfslineno as getfslineno
from ..compat import NOTSET as NOTSET, NotSetType as NotSetType, TYPE_CHECKING as TYPE_CHECKING, ascii_escaped as ascii_escaped, overload as overload
from _pytest.config import Config as Config
from _pytest.fixtures import _Scope
from _pytest.outcomes import fail as fail
from _pytest.warning_types import PytestUnknownMarkWarning as PytestUnknownMarkWarning
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Tuple, Type, Union

EMPTY_PARAMETERSET_OPTION: str

def istestfunc(func: Any) -> bool: ...
def get_empty_parameterset_mark(config: Config, argnames: Sequence[str], func: Any) -> MarkDecorator: ...

class ParameterSet:
    @classmethod
    def param(cls: Any, *values: object, marks: Union[MarkDecorator, typing.Collection[Union[MarkDecorator, Mark]]]=..., id: Optional[str]=...) -> ParameterSet: ...
    @classmethod
    def extract_from(cls: Any, parameterset: Union[ParameterSet, Sequence[object], object], force_tuple: bool=...) -> ParameterSet: ...

class Mark:
    name: Any = ...
    args: Any = ...
    kwargs: Any = ...
    def combined_with(self, other: Mark) -> Mark: ...
    def __init__(self, name: Any, args: Any, kwargs: Any, param_ids_from: Any, param_ids_generated: Any) -> None: ...
    def __lt__(self, other: Any) -> Any: ...
    def __le__(self, other: Any) -> Any: ...
    def __gt__(self, other: Any) -> Any: ...
    def __ge__(self, other: Any) -> Any: ...

class MarkDecorator:
    mark: Any = ...
    @property
    def name(self) -> str: ...
    @property
    def args(self) -> Tuple[Any, ...]: ...
    @property
    def kwargs(self) -> Mapping[str, Any]: ...
    @property
    def markname(self) -> str: ...
    def with_args(self, *args: object, **kwargs: object) -> MarkDecorator: ...
    def __call__(self, *args: object, **kwargs: object) -> Any: ...
    def __init__(self, mark: Any) -> None: ...
    def __lt__(self, other: Any) -> Any: ...
    def __le__(self, other: Any) -> Any: ...
    def __gt__(self, other: Any) -> Any: ...
    def __ge__(self, other: Any) -> Any: ...

def get_unpacked_marks(obj: Any) -> List[Mark]: ...
def normalize_mark_list(mark_list: Iterable[Union[Mark, MarkDecorator]]) -> List[Mark]: ...
def store_mark(obj: Any, mark: Mark) -> None: ...

class _SkipMarkDecorator(MarkDecorator):
    def __call__(self, reason: str=...) -> MarkDecorator: ...

class _SkipifMarkDecorator(MarkDecorator):
    def __call__(self, condition: Union[str, bool]=..., *conditions: Union[str, bool], reason: str=...) -> MarkDecorator: ...

class _XfailMarkDecorator(MarkDecorator):
    def __call__(self, condition: Union[str, bool]=..., *conditions: Union[str, bool], reason: str=..., run: bool=..., raises: Union[Type[BaseException], Tuple[Type[BaseException], ...]]=..., strict: bool=...) -> MarkDecorator: ...

class _ParametrizeMarkDecorator(MarkDecorator):
    def __call__(self, argnames: Union[str, List[str], Tuple[str, ...]], argvalues: Iterable[Union[ParameterSet, Sequence[object], object]], *, indirect: Union[bool, Sequence[str]]=..., ids: Optional[Union[Iterable[Union[None, str, float, int, bool]], Callable[[Any], Optional[object]]]]=..., scope: Optional[_Scope]=...) -> MarkDecorator: ...

class _UsefixturesMarkDecorator(MarkDecorator):
    def __call__(self, *fixtures: str) -> MarkDecorator: ...

class _FilterwarningsMarkDecorator(MarkDecorator):
    def __call__(self, *filters: str) -> MarkDecorator: ...

class MarkGenerator:
    skip: Any = ...
    skipif: Any = ...
    xfail: Any = ...
    parametrize: Any = ...
    usefixtures: Any = ...
    filterwarnings: Any = ...
    def __getattr__(self, name: str) -> MarkDecorator: ...

MARK_GEN: MarkGenerator

class NodeKeywords(collections.abc.MutableMapping):
    node: Any = ...
    parent: Any = ...
    def __init__(self, node: Any) -> None: ...
    def __getitem__(self, key: Any): ...
    def __setitem__(self, key: Any, value: Any) -> None: ...
    def __delitem__(self, key: Any) -> None: ...
    def __iter__(self) -> Any: ...
    def __len__(self) -> int: ...