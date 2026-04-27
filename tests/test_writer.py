from pathlib import Path

import polars as pl

from gems_views_builder.writer import Writer


def test_consolidate_results_returns_none_when_no_chunks(tmp_path: Path) -> None:
    writer = Writer(tmp_path)
    assert writer.consolidate_results([]) is None


def test_consolidate_results_merges_chunks_and_deletes_parts(tmp_path: Path) -> None:
    writer = Writer(tmp_path)

    chunk1 = tmp_path / "chunk1.parquet"
    chunk2 = tmp_path / "chunk2.parquet"

    pl.DataFrame({"metric_id": ["A"], "metric_value": [1.0]}).write_parquet(chunk1)
    pl.DataFrame({"metric_id": ["B"], "metric_value": [2.0]}).write_parquet(chunk2)

    out_path = writer.consolidate_results([chunk1, chunk2])
    assert out_path is not None
    assert out_path.is_file()
    assert out_path.parent == tmp_path / "results"

    # Ensure parts were cleaned up
    assert not chunk1.exists()
    assert not chunk2.exists()

    # Ensure output contains both rows (order not guaranteed)
    df = pl.read_parquet(out_path).select(["metric_id", "metric_value"]).sort("metric_id")
    assert df.to_dict(as_series=False) == {"metric_id": ["A", "B"], "metric_value": [1.0, 2.0]}
