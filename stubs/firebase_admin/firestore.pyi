from typing import Any, Optional

existing: Any

def client(app: Optional[Any] = ...): ...

class _FirestoreClient:
    def __init__(self, credentials: Any, project: Any) -> None: ...
    def get(self): ...
    @classmethod
    def from_app(cls, app: Any): ...