# Calculating Pi - PySpark implementation

This project estimates the value of Pi using the Monte Carlo method in a PySpark job on Google Cloud Platform (GCP). The concept involves randomly throwing darts at a board and calculating the ratio of darts that land inside a circle to estimate Pi.

## Project Overview

The program calculates Pi by throwing `N` number of darts onto a board, which land at random positions `(x, y)`. It checks if a dart lands inside a unit circle using the condition `x^2 + y^2 < r`. The ratio of darts that land inside the circle `S` to the total number of darts thrown `N`, multiplied by 4, gives the estimated value of Pi:

```
pi = 4 * S / N
```

![alt text](image.png)

## Steps to Run the Project on GCP

### 1. Create a Bucket and Set Up Dataproc

- Create a bucket in Google Cloud Storage (GCS).
- Set up a Dataproc cluster in the same region as your bucket.

### 2. Create and Save the Spark Job Python File

Activate the Cloud Shell and create the Python script:

```bash
vim calculatePi.py
```

Copy the following Python code into `calculatePi.py`:

```python
import argparse
import logging
from operator import add
from random import random

from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def calculate_pi(partitions, output_uri):
    """
    Calculates pi by testing a large number of random numbers against a unit circle
    inscribed inside a square. The trials are partitioned so they can be run in
    parallel on cluster instances.

    :param partitions: The number of partitions to use for the calculation.
    :param output_uri: The URI where the output is written, typically an Amazon S3
                       bucket, such as 's3://example-bucket/pi-calc'.
    """

    def calculate_hit(_):
        x = random() * 2 - 1
        y = random() * 2 - 1
        return 1 if x ** 2 + y ** 2 < 1 else 0

    tries = 100000 * partitions

    logger.info(
        "Calculating pi with a total of %s tries in %s partitions.", tries, partitions)

    with SparkSession.builder.appName("My PyPi").getOrCreate() as spark:
        hits = spark.sparkContext.parallelize(range(tries), partitions)\
            .map(calculate_hit)\
            .reduce(add)
        pi = 4.0 * hits / tries

        logger.info("%s tries and %s hits gives pi estimate of %s.", tries, hits, pi)

        if output_uri is not None:
            df = spark.createDataFrame(
                [(tries, hits, pi)], ['tries', 'hits', 'pi'])
            df.write.mode('overwrite').json(output_uri)


if __name__ == "__main__":
    parsers = argparse.ArgumentParser()
    parsers.add_argument(
        '--partitions', default=2, type=int,
        help="The number of parallel partitions to use when calculating pi.")
    parsers.add_argument(
        '--output_uri', help="The URI where output is saved, typically an S3 bucket.")
    args = parsers.parse_args()

    calculate_pi(args.partitions, args.output_uri)
```

### 3. Upload the Python Script to Your GCS Bucket

Upload the `calculatePi.py` file to your GCS bucket:
- first activate cloud shell
- Use you own bucket name , replace the bigdata_pyspark with your own

```bash
gsutil cp calculatePi.py gs://your-bucket-name
```

### 4. Submit the PySpark Job to Dataproc

Authenticate and submit the job to Dataproc:

```bash
gcloud auth login
gcloud dataproc jobs submit pyspark gs://your-bucket-name/calculatePi.py \
    --cluster=your-cluster-name \
    --region=your-region \
    -- \
    --partitions=4 \
    --output_uri=gs://your-bucket-name/pi-output
```

### 5. View the Output

List the output files in your GCS bucket:

```bash
gsutil ls gs://your-bucket-name/pi-output
```

Display the content of the output files:

```bash
gsutil cat gs://your-bucket-name/pi-output/*.json
```

## Command Line Arguments

- `--partitions` (default: 2): Specifies the number of parallel partitions to use when calculating Pi.
- `--output_uri`: Specifies the URI where the output will be saved (e.g., a GCS bucket).

### Example Command

```bash
--partitions 4 --output_uri gs://your-bucket-name/pi-output
```

### Sample Output

```
INFO: Calculating pi with a total of 400000 tries in 4 partitions.
INFO: 400000 tries and 314195 hits give a pi estimate of 3.14195.
```

## Explanation

The program accepts two command line arguments:

- `--partitions`: Specifies the number of parallel partitions to use when calculating Pi.
- `--output_uri`: Specifies the URI where the output will be saved.

The program runs the `calculate_pi` function with the provided arguments, generating random points and testing them against a unit circle. The work is distributed among partitions for parallel execution. The estimated value of Pi is logged and, if an output URI is provided, the results are saved as a JSON file in the specified location.

## Prerequisites

- Google Cloud SDK installed and configured.
- A GCS bucket and Dataproc cluster set up in the same region.

## Conclusion

This project demonstrates how to use PySpark on GCP to estimate the value of Pi using the Monte Carlo method. The steps include setting up the environment, creating and uploading the Python script, submitting the PySpark job, and viewing the results.



Feel free to modify this README file according to your specific requirements and environment details.