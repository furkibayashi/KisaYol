"""Kalıp modeli, tetikleyici doğrulama ve snippets.json deposu."""
from __future__ import annotations

import copy
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from typing import Callable, List, Optional

DEFAULT_GROUP = "Genel"
METHODS = ("paste", "type")


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Snippet:
    trigger: str
    text: str
    group: str = DEFAULT_GROUP
    method: str = "paste"
    enabled: bool = True
    id: str = field(default_factory=_new_id)


DEFAULT_SNIPPETS: List[Snippet] = [
    Snippet(";tarih", "{tarih}", id="default-tarih"),
    Snippet(";mail", "ornek@eposta.com", id="default-mail"),
    Snippet(";imza", "Saygılarımla,\n{imleç}", id="default-imza"),
]


def is_symbol_trigger(trigger: str) -> bool:
    """İlk karakteri harf/rakam değilse sembollü tetikleyicidir (anında genişler)."""
    return bool(trigger) and not trigger[0].isalnum()


def validate_trigger(trigger: str, others: List[Snippet], self_id: Optional[str] = None) -> Optional[str]:
    """Hata için i18n anahtarı, geçerliyse None döner."""
    if not trigger:
        return "err_empty"
    if any(ch.isspace() for ch in trigger):
        return "err_space"
    if len(trigger) < 2:
        return "err_short"
    symbol = is_symbol_trigger(trigger)
    if not symbol and not trigger.isalnum():
        return "err_bare_not_alnum"
    rest = [s for s in others if s.id != self_id]
    if any(s.trigger == trigger for s in rest):
        return "err_duplicate"
    if symbol:
        for s in rest:
            if not s.enabled or not is_symbol_trigger(s.trigger):
                continue
            if s.trigger.startswith(trigger) or trigger.startswith(s.trigger):
                return "err_prefix_conflict"
    return None


def _from_dict(d) -> Optional[Snippet]:
    if not isinstance(d, dict):
        return None
    trigger, text = d.get("trigger"), d.get("text")
    if not isinstance(trigger, str) or not isinstance(text, str):
        return None
    group = d.get("group") if isinstance(d.get("group"), str) and d.get("group").strip() else DEFAULT_GROUP
    method = d.get("method") if d.get("method") in METHODS else "paste"
    enabled = d.get("enabled") if isinstance(d.get("enabled"), bool) else True
    sid = d.get("id") if isinstance(d.get("id"), str) and d.get("id") else _new_id()
    return Snippet(trigger, text.replace("\r\n", "\n"), group, method, enabled, sid)


class SnippetStore:
    def __init__(self, path: str):
        self.path = path
        self.snippets: List[Snippet] = []
        self.groups: List[str] = [DEFAULT_GROUP]
        self.on_change: Optional[Callable[[], None]] = None

    # --- disk ---
    def load(self) -> None:
        if not os.path.exists(self.path):
            self._reset_defaults()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("snippets.json kök nesnesi sözlük değil")
        except Exception:
            self._backup_corrupt()
            self._reset_defaults()
            return
        self.snippets = []
        self.groups = [DEFAULT_GROUP]
        for g in data.get("groups") or []:
            if isinstance(g, str) and g.strip() and g not in self.groups:
                self.groups.append(g)
        for raw in data.get("snippets") or []:
            self._accept(_from_dict(raw))

    def save(self) -> None:
        payload = {
            "version": 1,
            "groups": list(self.groups),
            "snippets": [asdict(s) for s in self.snippets],
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def _backup_corrupt(self) -> None:
        try:
            os.replace(self.path, self.path + ".bak")
        except OSError:
            pass

    def _reset_defaults(self) -> None:
        self.snippets = [copy.deepcopy(s) for s in DEFAULT_SNIPPETS]
        self.groups = [DEFAULT_GROUP]

    def _accept(self, s: Optional[Snippet]) -> Optional[str]:
        """Bir kaydı ekler. 'skipped' / 'disabled' / None döner."""
        if s is None:
            return "skipped"
        err = validate_trigger(s.trigger, self.snippets, self_id=s.id)
        if err in ("err_empty", "err_space", "err_short", "err_bare_not_alnum", "err_duplicate"):
            return "skipped"
        if any(x.id == s.id for x in self.snippets):
            s.id = _new_id()
        status = None
        if err == "err_prefix_conflict" and s.enabled:
            s.enabled = False
            status = "disabled"
        self.snippets.append(s)
        if s.group not in self.groups:
            self.groups.append(s.group)
        return status

    # --- değişiklik ---
    def _changed(self) -> None:
        if self.on_change:
            self.on_change()

    def add(self, s: Snippet) -> None:
        self.snippets.append(s)
        if s.group not in self.groups:
            self.groups.append(s.group)
        self._changed()

    def update(self, s: Snippet) -> None:
        for i, x in enumerate(self.snippets):
            if x.id == s.id:
                self.snippets[i] = s
                break
        if s.group not in self.groups:
            self.groups.append(s.group)
        self._changed()

    def remove(self, sid: str) -> None:
        self.snippets = [s for s in self.snippets if s.id != sid]
        self._changed()

    def active(self) -> List[Snippet]:
        return [s for s in self.snippets if s.enabled]

    # --- içe / dışa aktarma ---
    def export_to(self, path: str) -> None:
        payload = {"version": 1, "groups": list(self.groups),
                   "snippets": [asdict(s) for s in self.snippets]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def import_from(self, path: str) -> List[str]:
        """Kalıpları ekler; devre dışı alınan ya da zaten var olduğu için atlanan tetikleyicileri döner."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("geçersiz kalıp dosyası")
        for g in data.get("groups") or []:
            if isinstance(g, str) and g.strip() and g not in self.groups:
                self.groups.append(g)
        flagged = []
        for raw in data.get("snippets") or []:
            s = _from_dict(raw)
            if s is None:
                continue
            s.id = _new_id()
            status = self._accept(s)
            if status == "disabled" or (status == "skipped" and
                                        any(x.trigger == s.trigger for x in self.snippets)):
                flagged.append(s.trigger)
        self._changed()
        return flagged
