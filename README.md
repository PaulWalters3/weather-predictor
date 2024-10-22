# weather-predictor

Collection of scripts for use in artificial neural network for predicting weather conditions 12 hours in the future.

The scripts include tools for generating training files for training and tools for running predictions from trained networks using current conditions.

These scripts were generated to use the NEURAL program from Practical Neural Network Recipes in C++.

The scripts assume the data has been collected into the database tables identified in tools/schema.sql.  One of the sites is considered the prediction site and the other collected site data is expected to be able to be used to predict the weather conditions for the prediction site.
