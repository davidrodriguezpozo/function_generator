# Generate [polars methods for python](https://pola.rs/), given the URL of a Microsoft Excel method page.



Example: 

```python


res = generate_method_from_url('https://support.microsoft.com/en-us/office/covariance-p-function-6f0e1e6d-956d-4e4b-9943-cfef0bf9edfc')
print(res)

```

Output:

```python
import polars as pl

def covariance_p(*args):
    # Ensure there are exactly two arguments
    if len(args) != 2:
        raise ValueError("COVARIANCE.P function requires exactly two arguments")

    array1, array2 = args

    # Calculate mean of both arrays
    mean1 = array1.mean()
    mean2 = array2.mean()

    # Calculate the covariance using the definition provided in the problem statement
    covariance = (array1 - mean1) * (array2 - mean2)
    covariance = covariance.sum() / array1.len()

    return covariance

def test():
    # Create test data, identical to the example used in "extra"
    df = pl.DataFrame({
        "Data1": [3, 2, 4, 5, 6],
        "Data2": [9, 7, 12, 15, 17]
    })

    # Create expressions for the columns
    data1_expr = pl.col("Data1")
    data2_expr = pl.col("Data2")

    # Calculate covariance using the function
    result_expr = covariance_p(data1_expr, data2_expr)

    # Calculate the result via execution on the dataframe
    result = df.select(result_expr).item()

    # Assert the result is as expected
    expected_result = 5.2
    assert result == expected_result, f"Expected {expected_result}, but got {result}"
```

## Requirements

- Python 3.6+
- requests
- beautifulsoup4
- openai
