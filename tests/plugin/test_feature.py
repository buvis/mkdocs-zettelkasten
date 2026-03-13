import pytest

from mkdocs_zettelkasten.plugin.feature import Feature, resolve_features


class _StubFeature:
    def __init__(self, name, depends_on=(), enabled=True):
        self.name = name
        self.depends_on = depends_on
        self.extra_key = None
        self._enabled = enabled

    def is_enabled(self, config):  # noqa: ARG002
        return self._enabled

    def compute(self, ctx):
        pass

    def export(self, ctx, files, config):
        pass

    def adapt_page(self, page, ctx):
        pass


class TestFeatureProtocol:
    def test_stub_satisfies_protocol(self) -> None:
        assert isinstance(_StubFeature("test"), Feature)


class TestResolveFeatures:
    def test_empty_list(self) -> None:
        assert resolve_features([], None) == []

    def test_filters_disabled(self) -> None:
        a = _StubFeature("a", enabled=True)
        b = _StubFeature("b", enabled=False)
        result = resolve_features([a, b], None)
        assert result == [a]

    def test_preserves_order_no_deps(self) -> None:
        a = _StubFeature("a")
        b = _StubFeature("b")
        result = resolve_features([a, b], None)
        assert result == [a, b]

    def test_sorts_by_dependency(self) -> None:
        a = _StubFeature("a", depends_on=("b",))
        b = _StubFeature("b")
        result = resolve_features([a, b], None)
        assert result == [b, a]

    def test_deep_dependency_chain(self) -> None:
        c = _StubFeature("c")
        b = _StubFeature("b", depends_on=("c",))
        a = _StubFeature("a", depends_on=("b",))
        result = resolve_features([a, b, c], None)
        names = [f.name for f in result]
        assert names.index("c") < names.index("b") < names.index("a")

    def test_missing_dependency_ignored(self) -> None:
        a = _StubFeature("a", depends_on=("nonexistent",))
        result = resolve_features([a], None)
        assert result == [a]

    def test_disabled_dependency_skipped(self) -> None:
        a = _StubFeature("a", depends_on=("b",))
        b = _StubFeature("b", enabled=False)
        result = resolve_features([a, b], None)
        assert result == [a]

    def test_circular_dependency_raises(self) -> None:
        a = _StubFeature("a", depends_on=("b",))
        b = _StubFeature("b", depends_on=("a",))
        with pytest.raises(ValueError, match="Circular"):
            resolve_features([a, b], None)

    def test_diamond_dependency(self) -> None:
        d = _StubFeature("d")
        b = _StubFeature("b", depends_on=("d",))
        c = _StubFeature("c", depends_on=("d",))
        a = _StubFeature("a", depends_on=("b", "c"))
        result = resolve_features([a, b, c, d], None)
        names = [f.name for f in result]
        assert names.index("d") < names.index("b")
        assert names.index("d") < names.index("c")
        assert names.index("b") < names.index("a")
        assert names.index("c") < names.index("a")
