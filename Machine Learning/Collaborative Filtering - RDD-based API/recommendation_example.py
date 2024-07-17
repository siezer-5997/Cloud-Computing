"""
Collaborative Filtering Classification Example.
"""
from pyspark import SparkContext

# $example on$
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating
# $example off$

if __name__ == "__main__":
    sc = SparkContext(appName="PythonCollaborativeFilteringExample")
    # $example on$
    # Load and parse the data
    # - Each row consists of a user, a product and a rating.
    data = sc.textFile("gs://big_data_movie_recommendation/u_transformed_data.csv")

    # Each line is 
    ratings = data.map(lambda l: l.split(','))\
        .map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

    # Build the recommendation model using ALS
    # - rank: number of features to use
    rank = 10

    # - iterattions: number of iterations of ALS (recommended: 10-20)
    numIterations = 10

    # The default ALS.train() method which assumes ratings are explicit.
    # - Train a matrix factorization model given an RDD of ratings given by 
    #   users to some products, in the form of (userID, productID, rating) pairs. 
    # - We approximate the ratings matrix as the product of two lower-rank 
    #   matrices of a given rank (number of features). 
    #   + To solve for these features, we run a given number of 
    #     iterations of ALS. 
    #   + The level of parallelism is determined automatically based 
    #     on the number of partitions in ratings.  
    model = ALS.train(ratings, rank, numIterations)

    ############################################################
    # Evaluate the model on training data
    # - Evaluate the recommendation model on rating training data
    ############################################################
    testdata = ratings.map(lambda p: (p[0], p[1]))
    predictions = model.predictAll(testdata).map(lambda r: ((r[0], r[1]), r[2]))


    # Join input rating ((user, product), rate1) with predicted rating 
    # ((user, product), rate2) to create ((user, product), (rate1, rate2))
    ratesAndPreds = ratings.map(lambda r: ((r[0], r[1]), r[2])).join(predictions)
    MSE = ratesAndPreds.map(lambda r: (r[1][0] - r[1][1])**2).mean()
    print("Mean Squared Error = " + str(MSE))

    # Save and load model
    model.save(sc, "target/tmp/myCollaborativeFilter")
    sameModel = MatrixFactorizationModel.load(sc, "target/tmp/myCollaborativeFilter")
    # $example off$