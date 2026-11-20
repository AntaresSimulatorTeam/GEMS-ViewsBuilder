# Copyright 2007-2026, RTE (https://www.rte-france.com)
# SPDX-License-Identifier: MPL-2.0

"""Deterministic integer ids for (component, output) pairs.

Both the filtered simulation table and the metric structure table derive the same
``pair_id`` from the same (component, output) strings with MurmurHash3, so the two
tables can be joined on a single Int64 column instead of two string columns,
without sharing any dictionary between them.
"""

import bisect
import hashlib
import os
from collections.abc import Iterable
from functools import cache

import mmh3
import polars as pl

# ASCII "unit separator": cannot appear in component / output ids, so
# ("a", "bc") and ("ab", "c") never hash the same input.
_SEPARATOR = "\x1f"

# Upper bound on the number of on-disk clusters of the filtered simulation table.
MAX_PAIR_BUCKETS = 64

PAIR_LOOKUP_SCHEMA = pl.Schema(
    {
        "component": pl.String,
        "output": pl.String,
        "pair_id": pl.Int64,
        "pair_bucket": pl.Int64,
    }
)


def make_pair_id(component: str, output: str) -> int:
    """64-bit signed MurmurHash3 (x64, 128-bit variant, first half) of the pair."""
    return mmh3.hash64(f"{component}{_SEPARATOR}{output}", signed=True)[0]


def bucket_count_for(pair_count: int) -> int:
    if PAIR_BUCKETING == "none":  # experimental single filtered table, no buckets
        return 1
    return max(1, min(MAX_PAIR_BUCKETS, pair_count))


def bucket_of(pair_id: int, bucket_count: int) -> int:
    if PAIR_BUCKET_CACHE:
        return _cached_bucket_of(pair_id, bucket_count)
    return _bucket_of(pair_id, bucket_count)


def _bucket_of(pair_id: int, bucket_count: int) -> int:
    if PAIR_BUCKETING == "ring":
        return _ring_bucket_of(pair_id, bucket_count)
    # Python's modulo is always non-negative for a positive divisor.
    return pair_id % bucket_count


# Experimental: GVB_PAIR_BUCKET_CACHE=1 remembers each pair's bucket, so a pair read by several
# metrics is only located once.
PAIR_BUCKET_CACHE = os.environ.get("GVB_PAIR_BUCKET_CACHE", "0") == "1"
_cached_bucket_of = cache(_bucket_of)


# Experimental alternative to the modulo: consistent-hashing ring (Karger et al. 1997, CS168 L1).
# GVB_PAIR_BUCKETING=ring places each bucket at RING_VIRTUAL_NODES SHA3 positions on [0, 2^32 - 1];
# a pair belongs to the first position clockwise from sha3(pair_id).
PAIR_BUCKETING = os.environ.get("GVB_PAIR_BUCKETING", "modulo")
RING_VIRTUAL_NODES = int(os.environ.get("GVB_RING_VIRTUAL_NODES", "1024"))


def _ring_position(data: bytes) -> int:
    return int.from_bytes(hashlib.sha3_256(data).digest()[:4], "big")


@cache
def _ring(bucket_count: int) -> tuple[list[int], list[int]]:
    circle = {
        _ring_position(f"bucket-{b}#{i}".encode()): b
        for b in range(bucket_count)
        for i in range(RING_VIRTUAL_NODES)
    }
    positions = sorted(circle)
    return positions, [circle[p] for p in positions]


def _ring_bucket_of(pair_id: int, bucket_count: int) -> int:
    positions, owners = _ring(bucket_count)
    i = bisect.bisect_left(positions, _ring_position(pair_id.to_bytes(8, "big", signed=True)))
    return owners[i % len(positions)]  # past the last position, wrap around to the first


def make_pair_lookup(pairs: Iterable[tuple[str, str]], bucket_count: int) -> pl.DataFrame:
    """Build the (component, output) -> (pair_id, pair_bucket) table, raising on hash collisions."""
    unique_pairs = sorted(set(pairs))
    ids = [make_pair_id(component, output) for component, output in unique_pairs]
    if len(set(ids)) != len(ids):
        raise ValueError("MurmurHash3 collision between two (component, output) pairs")
    return pl.DataFrame(
        {
            "component": [component for component, _ in unique_pairs],
            "output": [output for _, output in unique_pairs],
            "pair_id": ids,
            "pair_bucket": [bucket_of(i, bucket_count) for i in ids],
        },
        schema=PAIR_LOOKUP_SCHEMA,
    )
