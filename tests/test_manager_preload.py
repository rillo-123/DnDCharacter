import builtins
import sys
import types
import pytest

import character


def test_ensure_manager_loaded_http_fallback(monkeypatch):
    # Ensure no pre-existing module
    sys.modules.pop("foo_manager", None)

    # Make standard import fail for foo_manager
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "foo_manager":
            raise ImportError("No module named 'foo_manager'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # Create a fake module that would be returned by the HTTP loader
    fake_mod = types.SimpleNamespace()

    def initialize_foo_manager(*args, **kwargs):
        return "ok"

    fake_mod.initialize_foo_manager = initialize_foo_manager

    def fake_http_loader(module_name, url, _retry=True):
        assert module_name == "foo_manager"
        return fake_mod

    monkeypatch.setattr(character, "_load_module_from_http_sync", fake_http_loader)

    func = character._ensure_manager_loaded(
        "foo_manager",
        "initialize_foo_manager",
        "http://localhost:8080/assets/py/foo_manager.py",
    )

    assert callable(func)
    assert func() == "ok"


def test_ensure_manager_loaded_raises_if_not_found(monkeypatch):
    sys.modules.pop("bar_manager", None)

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "bar_manager":
            raise ImportError("No module named 'bar_manager'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError):
        character._ensure_manager_loaded("bar_manager", "initialize_bar_manager")
