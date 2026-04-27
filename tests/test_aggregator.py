from pathlib import Path

import polars as pl

from gems_views_builder.aggregator import Aggregator
from gems_views_builder.catalog import TermsOperator, TimeOperator
from gems_views_builder.views import ViewBuilder


def _joined_df(values: list[float]) -> pl.LazyFrame:
    """
    Minimal columns required by Aggregator.aggregate_metric_terms().

    """
    return pl.DataFrame(
        {
            "metric_id": ["M"] * len(values),
            "metric_location": ["L"] * len(values),
            "breakdown_properties": [""] * len(values),
            "absolute_time_index": [1] * len(values),
            "scenario_index": [0] * len(values),
            "value": values,
            # at least one non-null per group, strings are fine for grouping here
            "granular_date": ["2026-01-01"] * len(values),
        }
    ).lazy()


def test_aggregate_metric_terms_sum(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    out_path = agg.aggregate_metric_terms(_joined_df([2.0, 3.0]), TermsOperator.SUM, metric_id="M")

    df = pl.read_parquet(out_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == 5.0


def test_aggregate_metric_terms_avg(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)
    out_path = agg.aggregate_metric_terms(_joined_df([2.0, 3.0]), TermsOperator.AVG, metric_id="M")

    df = pl.read_parquet(out_path)
    assert df.shape[0] == 1
    assert df["granular_metric_value"][0] == 2.5


def test_aggregate_metric_temporally_sum_and_part_counter(tmp_path: Path) -> None:
    agg = Aggregator(tmp_path)

    metric_view_path = agg.aggregate_metric_terms(_joined_df([1.0, 2.0]), TermsOperator.SUM, metric_id="M")

    part0 = agg.aggregate_metric_temporally(metric_view_path, TimeOperator.SUM, metric_id="M")
    df0 = pl.read_parquet(part0)
    assert df0.shape[0] == 1
    assert df0["metric_value"][0] == 3.0

    part1 = agg.aggregate_metric_temporally(metric_view_path, TimeOperator.SUM, metric_id="M")
    assert part1 != part0
    assert part0.name.endswith("-0.parquet")
    assert part1.name.endswith("-1.parquet")


def test_aggregator_integration_build_writes_final_result_and_cleans_chunks(
    test_files_root: Path, tmp_path: Path
) -> None:
    """
    Integration smoke test on a real dataset from tests.zip.

    ViewBuilder uses Aggregator to create temporal chunk parquets, then Writer
    consolidates them into a single result and deletes the chunks.
    """
    import shutil

    src = test_files_root / "test_3"
    dst = tmp_path / "test_3"
    shutil.copytree(src, dst)

    ViewBuilder(dst).build()

    result_files = sorted((dst / "results").glob("*.parquet"))
    assert result_files, "Expected a consolidated result parquet to be written"

    # Sanity check: result is readable and contains at least one row.
    df = pl.read_parquet(result_files[0])
    assert df.height > 0

    # Chunks should have been deleted by Writer.consolidate_results().
    chunk_parts = sorted((dst / "temporal_aggregation").glob("*.parquet"))
    assert not chunk_parts
