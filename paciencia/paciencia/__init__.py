"""Paciência: Klondike, FreeCell e Spider sobre uma base comum (base.py)."""
from .freecell import FreeCell
from .klondike import Klondike
from .spider import Spider

GAMES = {g.ID: g for g in (Klondike, FreeCell, Spider)}
ORDER = (Klondike, FreeCell, Spider)
