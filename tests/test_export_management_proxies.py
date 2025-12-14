import sys
import types

import export_management as em


class _DummyClassList(set):
    def add(self, *tokens):
        for token in tokens:
            super().add(token)

    def remove(self, *tokens):
        for token in tokens:
            super().discard(token)


class _DummyStyle:
    def __init__(self):
        self.display = ""
        self.opacity = ""
        self.visibility = ""


class _DummyIndicator:
    def __init__(self):
        self.classList = _DummyClassList()
        self.style = _DummyStyle()


class _DummyDocument:
    def __init__(self, indicator):
        self._indicator = indicator
        self.defaultView = None

    def getElementById(self, element_id):
        if element_id == "saving-indicator":
            return self._indicator
        return None


class _DummyWindow:
    def __init__(self):
        self._calls = []

    def setTimeout(self, callback, timeout):
        # Record the callback; tests assert it is a proxy object
        self._calls.append((callback, timeout))
        return len(self._calls)

    def getComputedStyle(self, element):
        return types.SimpleNamespace(display="flex", opacity="1", visibility="visible")


class _DummyStorage(dict):
    def setItem(self, key, value):
        self[key] = value


def _install_env(monkeypatch):
    indicator = _DummyIndicator()
    window = _DummyWindow()
    document = _DummyDocument(indicator)
    document.defaultView = window

    # Reset export state
    monkeypatch.setattr(em, "window", window)
    monkeypatch.setattr(em, "document", document)
    monkeypatch.setattr(em, "localStorage", _DummyStorage())
    monkeypatch.setattr(em, "_AUTO_EXPORT_DISABLED", False)
    monkeypatch.setattr(em, "_AUTO_EXPORT_SUPPRESS", False)
    monkeypatch.setattr(em, "_AUTO_EXPORT_TIMER_ID", None)
    monkeypatch.setattr(em, "_AUTO_EXPORT_EVENT_COUNT", 0)
    monkeypatch.setattr(em, "_EVENT_PROXIES", [])

    # Provide a fake character module with collect_character_data
    fake_character = types.SimpleNamespace(
        collect_character_data=lambda: {"identity": {"name": "Test"}, "level": 1}
    )
    monkeypatch.setitem(sys.modules, "character", fake_character)

    proxies = []

    class _ProxyWrapper:
        def __init__(self, func):
            self.func = func

    def fake_create_proxy(func):
        proxy = _ProxyWrapper(func)
        proxies.append((proxy, func))
        return proxy

    monkeypatch.setattr(em, "create_proxy", fake_create_proxy)

    return window, indicator, proxies


def test_schedule_auto_export_uses_asyncio_for_timeout(monkeypatch):
    """Test that schedule_auto_export uses asyncio.Task instead of setTimeout.
    
    The fix for borrowed proxy destruction is to use Python's asyncio.sleep()
    instead of JavaScript's setTimeout. This keeps the callback in Python
    and avoids proxy lifecycle issues.
    """
    import asyncio
    
    window, indicator, proxies = _install_env(monkeypatch)

    em.schedule_auto_export()

    # Should NOT create proxies anymore (we use asyncio instead of setTimeout)
    # The old test that checked for proxies is now obsolete
    assert not proxies, "Should not use create_proxy when using asyncio"

    # Should NOT have called setTimeout (using asyncio instead)
    assert not window._calls, "Should use asyncio.Task instead of setTimeout"

    # Instead, an asyncio Task should be scheduled
    assert em._AUTO_EXPORT_TIMER_ID is not None
    assert isinstance(em._AUTO_EXPORT_TIMER_ID, asyncio.Task)

    # Saving indicator should have been forced visible
    assert "recording" in indicator.classList
    assert indicator.style.display == "flex"
    assert indicator.style.opacity == "1"