## README.md

# Movie Recommendation with MLlib - Collaborative Filtering (Implementation 2)

## Project Overview
This project aims to build a movie recommendation system using collaborative filtering with PySpark and Google Cloud Dataproc. Collaborative filtering predicts user interests by collecting preferences from many users, making it an effective approach for recommendation systems.

## Table of Contents
- [Project Overview](#project-overview)
- [Data Preparation](#data-preparation)
- [Uploading Data to Cloud](#uploading-data-to-cloud)
- [PySpark Script](#pyspark-script)
- [Running the Job on Dataproc](#running-the-job-on-dataproc)
- [Results](#results)
- [Enhancement Ideas](#enhancement-ideas)
- [Conclusion](#conclusion)
- [References](#references)

## Data Preparation

### Step 1: Preparing and Transforming Data
1. **Download the MovieLens dataset** and save it as `u.data`.
2. **Transform the data**:
    - Create a bash script named `transform_data.sh`:
        ```bash
        #!/bin/bash
        cat u.data | while read userid movieid rating timestamp
        do
           echo "${userid},${movieid},${rating}"
        done > u_transformed_data.csv
        ```
    - Make the script executable:
        ```bash
        chmod +x transform_data.sh
        ```
    - Run the script to transform the data:
        ```bash
        ./transform_data.sh
        ```

The shell script reads each line of the `u.data` file, splits the data by spaces, and reformats it to display only the UserID, MovieID, and rating fields separated by commas. This transformation removes the timestamp field and formats the data into CSV format, which is easier to work with for further processing. The transformed data will be saved in the file `u_transformed_data.csv`.

## Uploading Data to Cloud

### Step 2: Upload Transformed Data to Cloud Storage
1. **Upload the transformed data** to your Google Cloud Storage bucket:
    ```bash
    gsutil cp u_transformed_data.csv gs://big_data_movie_recommendation
    ```

## PySpark Script

### Step 3: Create and Upload the PySpark Script
1. **Create a file named `recommendation_example.py`** and copy the following script into it:
    ```python
    """
    Collaborative Filtering Classification Example.
    """
    from pyspark import SparkContext
    from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating

    if __name__ == "__main__":
        sc = SparkContext(appName="PythonCollaborativeFilteringExample")

        # Load and parse the data
        data = sc.textFile("gs://big_data_movie_recommendation/u_transformed_data.csv")
        ratings = data.map(lambda l: l.split(','))\
            .map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

        # Build the recommendation model using ALS
        rank = 10
        numIterations = 10
        model = ALS.train(ratings, rank, numIterations)

        # Evaluate the model on training data
        testdata = ratings.map(lambda p: (p[0], p[1]))
        predictions = model.predictAll(testdata).map(lambda r: ((r[0], r[1]), r[2]))
        ratesAndPreds = ratings.map(lambda r: ((r[0], r[1]), r[2])).join(predictions)
        MSE = ratesAndPreds.map(lambda r: (r[1][0] - r[1][1])**2).mean()
        print("Mean Squared Error = " + str(MSE))

        # Save and load model
        model.save(sc, "target/tmp/myCollaborativeFilter")
        sameModel = MatrixFactorizationModel.load(sc, "target/tmp/myCollaborativeFilter")
    ```

2. **Upload the PySpark script** to your Google Cloud Storage bucket:
    ```bash
    gsutil cp recommendation_example.py gs://big_data_movie_recommendation
    ```

## Running the Job on Dataproc

### Step 4: Submit the PySpark Job to Google Dataproc
1. **Create a Google Cloud Dataproc cluster**:
    ```bash
    gcloud dataproc clusters create spark-cluster \
    --region us-west1 \
    --zone us-west1-a \
    --single-node
    ```

2. **Submit the PySpark job** to the Dataproc cluster:
    ```bash
    gcloud dataproc jobs submit pyspark gs://big_data_movie_recommendation/recommendation_example.py \
    --cluster spark-cluster \
    --region us-west1
    ```

## Results

### Output of the PySpark Job
- **Mean Squared Error**: The model's performance is evaluated by calculating the Mean Squared Error (MSE) of the predicted ratings compared to the actual ratings. In this project, the MSE was found to be `0.48435603686025513`.

## Enhancement Ideas
1. **Data Enrichment**: Incorporate additional data sources like user demographics or movie genres.
2. **Parameter Tuning**: Experiment with different ALS parameters (rank, iterations).
3. **Model Evaluation**: Use other evaluation metrics like Root Mean Squared Error (RMSE) or Mean Absolute Error (MAE).
4. **Scalability**: Optimize the PySpark code for larger datasets.
5. **User Interface**: Develop a user-friendly interface for the recommendation system.

## Conclusion
This project successfully built a movie recommendation system using collaborative filtering with PySpark and Google Cloud Dataproc. The system was evaluated using Mean Squared Error, achieving a value of `0.48435603686025513`. Future work could include data enrichment, parameter tuning, and developing a user interface.

## Appendix
- [Detailed PDF documentation of steps]()
- [Google Slides](https://docs.google.com/presentation/d/19bpe07ttWc1RhjUMqDQOlnlIEquXW73tn8slAYwzM2A/edit?usp=sharing)



## References
- [MovieLens Dataset](https://files.grouplens.org/datasets/movielens/ml-100k/u.data)
- [MLlib - Collaborative Filtering](https://spark.apache.org/docs/1.2.2/mllib-collaborative-filtering.html)

---
