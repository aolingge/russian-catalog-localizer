from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_value(cls, value: Any) -> "Box":
        if isinstance(value, dict):
            return cls(
                float(value["x0"]),
                float(value["y0"]),
                float(value["x1"]),
                float(value["y1"]),
            )
        if isinstance(value, (list, tuple)) and len(value) == 4:
            return cls(float(value[0]), float(value[1]), float(value[2]), float(value[3]))
        raise ValueError(f"Expected bbox as [x0, y0, x1, y1], got {value!r}")

    def to_list(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]


@dataclass
class Segment:
    page: int
    text: str
    bbox: Box
    confidence: float | None = None
    source: str = "ocr"
    translated_text: str | None = None
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Segment":
        bbox = data.get("bbox", data.get("box"))
        if bbox is None:
            raise ValueError(f"Segment is missing bbox: {data!r}")
        confidence = data.get("confidence")
        return cls(
            page=int(data["page"]),
            text=str(data.get("text", "")).strip(),
            bbox=Box.from_value(bbox),
            confidence=None if confidence is None else float(confidence),
            source=str(data.get("source", "ocr")),
            translated_text=data.get("translated_text"),
            notes=list(data.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "page": self.page,
            "text": self.text,
            "bbox": self.bbox.to_list(),
            "source": self.source,
        }
        if self.confidence is not None:
            data["confidence"] = self.confidence
        if self.translated_text is not None:
            data["translated_text"] = self.translated_text
        if self.notes:
            data["notes"] = self.notes
        return data
