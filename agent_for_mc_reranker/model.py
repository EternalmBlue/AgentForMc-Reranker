from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class BceReranker:
    model_name_or_path: str
    _model: Any | None = None
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def warmup(self) -> None:
        with self._lock:
            self._get_model()

    def compute_scores(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        pairs = [[query, passage] for passage in passages]
        with self._lock:
            model = self._get_model()
            scores = model.compute_score(pairs)
        return [float(score) for score in scores]

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        from BCEmbedding import RerankerModel

        self._model = RerankerModel(model_name_or_path=self.model_name_or_path)
        return self._model
