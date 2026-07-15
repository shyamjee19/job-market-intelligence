import os

import pytest

from ai.vectorstore.base import VectorRecord
from ai.vectorstore.memory_store import InMemoryVectorStore


@pytest.fixture
def store(tmp_path):
    return InMemoryVectorStore(path=str(tmp_path / "vectors.json"))


def test_query_ranks_closest_vector_first(store):
    store.upsert(
        [
            VectorRecord(id="a", vector=[1, 0, 0], text="python job", metadata={}),
            VectorRecord(id="b", vector=[0, 1, 0], text="unrelated job", metadata={}),
        ]
    )
    results = store.query([1, 0, 0], top_k=2)
    assert results[0].id == "a"
    assert results[0].score > results[1].score


def test_query_respects_top_k(store):
    store.upsert([VectorRecord(id=str(i), vector=[1, i, 0], text=f"job {i}", metadata={}) for i in range(10)])
    results = store.query([1, 0, 0], top_k=3)
    assert len(results) == 3


def test_query_on_empty_store_returns_empty_list(store):
    assert store.query([1, 0, 0], top_k=5) == []


def test_upsert_persists_to_disk_and_reloads(tmp_path):
    path = str(tmp_path / "vectors.json")
    store = InMemoryVectorStore(path=path)
    store.upsert([VectorRecord(id="a", vector=[1, 0], text="hello", metadata={"x": 1})])

    assert os.path.exists(path)

    reloaded = InMemoryVectorStore(path=path)
    assert reloaded.count() == 1
    match = reloaded.query([1, 0], top_k=1)[0]
    assert match.text == "hello"
    assert match.metadata == {"x": 1}


def test_upsert_overwrites_existing_id(store):
    store.upsert([VectorRecord(id="a", vector=[1, 0], text="first", metadata={})])
    store.upsert([VectorRecord(id="a", vector=[1, 0], text="second", metadata={})])
    assert store.count() == 1
    assert store.query([1, 0], top_k=1)[0].text == "second"
