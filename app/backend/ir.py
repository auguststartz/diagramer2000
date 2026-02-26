from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class IRRect:
    id: str
    x: int
    y: int
    width: int
    height: int
    radius: int
    stroke_width: int
    fill_color: str
    stroke_color: str
    label: str
    label_color: str
    label_font_size: int
    label_x_offset: int
    label_y_offset: int
    parent_id: str | None
    semantic_role: str


@dataclass
class IRText:
    id: str
    x: int
    y: int
    text: str
    color: str
    font_size: int
    semantic_role: str


@dataclass
class IRLine:
    id: str
    x1: int
    y1: int
    x2: int
    y2: int
    color: str
    width: int


@dataclass
class IRDot:
    id: str
    cx: int
    cy: int
    radius: int
    color: str


@dataclass
class IRIcon:
    id: str
    x: int
    y: int
    width: int
    height: int
    icon_key: str


IRElement = Union[IRRect, IRText, IRLine, IRDot, IRIcon]


@dataclass
class DiagramIR:
    canvas_width: int = 1920
    canvas_height: int = 1080
    elements: list[IRElement] = field(default_factory=list)
