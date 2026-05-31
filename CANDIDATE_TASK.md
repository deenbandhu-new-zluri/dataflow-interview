# Task: add an `aggregate` operator

DataFlow currently ships two transform operators — `filter` and `select`. We
want a third: **`aggregate`**, which groups rows by one or more columns and
computes summary values over each group (the data-warehouse `GROUP BY`).

## Behaviour

Given a pipeline step like:

```json
{
  "type": "aggregate",
  "config": {
    "groupBy": ["country"],
    "aggregations": [
      {"column": "amount", "op": "sum", "as": "total_amount"},
      {"column": "id",     "op": "count", "as": "events"}
    ]
  }
}
```

running it over the `events` source should produce one row per distinct
`country`, e.g.:

```json
[
  {"country": "US", "total_amount": 170, "events": 4},
  {"country": "IN", "total_amount": 100, "events": 3},
  {"country": "DE", "total_amount": 200, "events": 1}
]
```

Requirements:

- Support grouping by **one or more** columns.
- Support at least the aggregation ops **`sum`** and **`count`**. Add `avg`,
  `min`, `max` if you have time.
- Each output row contains the group-by columns plus one field per
  aggregation, named by its `as`.
- `validate` should reject malformed configs (missing `groupBy`, unknown `op`,
  missing `as`, etc.) with a clear message — consistent with how `filter` and
  `select` validate.

## Done means

1. A pipeline using `"type": "aggregate"` can be created and run through the
   API and produces the output above.
2. There are tests for it, following the existing test style.
3. `pytest` passes.

You don't need to touch the HTTP layer's shape or the storage layer. Treat the
codebase as yours — leave it in whatever state you'd be comfortable shipping and
having a teammate build on. Ask questions as you go.
