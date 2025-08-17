from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict

class Span(TypedDict, total=False):
    text: str
    size: float
    font: str
    flags: int
    bbox: List[float]

class TextBlock(TypedDict, total=False):
    type: str  # 'text'
    text: str
    bbox: List[float]
    spans: List[Span]

class ImageItem(TypedDict, total=False):
    id: str
    xref: int
    bbox: Optional[List[float]]
    path: Optional[str]
    alt: Optional[str]

class Page(TypedDict, total=False):
    number: int
    width: float
    height: float
    raw_blocks: List[TextBlock]
    images: List[ImageItem]
    links: List["LinkItem"]

class BlockOut(TypedDict, total=False):
    type: str  # 'heading' | 'paragraph'
    level: Optional[int]
    text: str
    bbox: List[float]

class PageOut(TypedDict, total=False):
    number: int
    width: float
    height: float
    blocks: List[BlockOut]
    images: List[ImageItem]
    links: List["LinkItem"]

class DocOut(TypedDict, total=False):
    meta: Dict[str, Any]
    pages: List[PageOut]

class TocItem(TypedDict, total=False):
    level: int
    title: str
    page: int

class LinkItem(TypedDict, total=False):
    bbox: List[float]
    uri: Optional[str]
    target_page: Optional[int]
    text: Optional[str]

class SectionBlock(TypedDict, total=False):
    page: int
    block: BlockOut

class SectionNode(TypedDict, total=False):
    title: str
    level: int
    page_start: int
    page_end: Optional[int]
    children: List["SectionNode"]
    blocks: List[SectionBlock]
    images: List[ImageItem]
    links: List[LinkItem]
