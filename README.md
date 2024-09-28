# Generate [polars methods for python](https://pola.rs/), given the URL of a Microsoft Excel method page.



Example: 

```python


res = generate_method_from_url('https://support.microsoft.com/en-us/office/covariance-p-function-6f0e1e6d-956d-4e4b-9943-cfef0bf9edfc')
print(res)

```

Output:

```python

import polars as pl

def covariance_p(*args: pl.Expr) -> pl.Expr:
    if len(args) != 2:
        raise ValueError("COVARIANCE.P function requires exactly two arguments")

    array1, array2 = args

    n = pl.sum((array1 * 0 + 1).cast(pl.Float64))
    avg_array1 = pl.mean(array1)
    avg_array2 = pl.mean(array2)

    covariance = ((array1 - avg_array1) * (array2 - avg_array2)).sum() / n

    return covariance

```

## Requirements

- Python 3.6+
- requests
- beautifulsoup4
- openai
