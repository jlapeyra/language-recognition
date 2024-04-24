#Here are some libraries you're likely to use. You might want/need others as well.
import re
import sys
from random import random
from math import log
from collections import defaultdict
import numpy as np
from numpy.core.defchararray import add
import matplotlib.pyplot as plt
import os

vocabulary = np.array(list(" #.0abcdefghijklmnopqrstuvwxyz"))
alpha_es = 0.09
alpha_en = 0.08
alpha_de = 0.10

def preprocess_line(line):
    """
    - line is a string.
    Returns a modification of 'line' to fit our vocabulary ('a'..'z', '.', ' ', '0', '#').
    It also adds '##' to mark the start and '#' to mark the end.
    """
    ret = ""
    for c in line:
        if ('a' <= c <= 'z') or c == ' ' or c == '.': ret += c
        elif 'A' <= c <= 'Z': ret += c.lower()
        elif '0' <= c <= '9': ret += '0'
    return "##"+ret+"#"  # is a symbol used to mark both the start and end of a sequence


def load_model_cumulative(model):
    """
    - model is a file representing a trigram language model.
    Returns a dictionary mapping pairs of characters XY to a list l [[Z1, P1], ..., [Z30, P30]]
    where Z1..Z30 is out alphabet (' '..'z') and Pi = sum(P(Zj|XY), j=1..i), given 1<=i<=30.
    """
    model_cum = defaultdict(list)
    hist = model.readline()[0:2]
    model.seek(0) # return to the begining of the file
    cumsum = 0
    for line in model:
        if hist != line[0:2]:
            model_cum[hist][-1][1] = 1.0
            cumsum = float(line[4:])
            hist = line[0:2]
        else:
            cumsum += float(line[4:])
        model_cum[hist].append([line[2], cumsum])
    return model_cum


def load_model(model_file):
    """
    - model is a file representing a trigram language model.
    Returns a dictionary mapping trios of characters XYZ to P(Z|XY).
    """
    model_dict = defaultdict(float)
    model_file.seek(0) # return to the beginning of the file
    for line in model_file:
        model_dict[line[0:3]] = float(line[4:])
    return model_dict
        

def generate_from_LM(model_name):
    """
    - model_name is a path to a file representing a trigram language model.
    Prints text based on hte model.
    """
    with open(model_name) as model:
        model_cum = load_model_cumulative(model)
        hist = '##'
        for i in range(300):
            r = np.random.random()
            next_char = next((x for x in model_cum[hist] if x[1] > r), None)
            if next_char[0] == '#':
                hist = '##'
                print()
            else:
                print(next_char[0], end='')
                hist = hist[1] + next_char[0]


def create_model(training_file, model_name, alpha):
    """
    - training_file is a path to a texts file used as a training set
    - model_name is a string
    - alpha is a non-negative real number, used for alpha-smoothing
    It creates a trigram language model using the training set. It uses maximum likelihood
     estimate with alpha-smoothing. It stores the model in a file named model_file
     with the same extension as training_file.
    """
    tri_counts=defaultdict(int) #counts of all trigrams in input
    bi_counts=defaultdict(int) #counts of all bigrams in input
    with open(training_file) as f:
        for line in f:
            line = preprocess_line(line)
            for j in range(len(line)-(2)):
                trigram = line[j:j+3]
                tri_counts[trigram] += 1
            for j in range(len(line)-(1)):
                bigram = line[j:j+2]
                bi_counts[bigram] += 1
    model_name = model_name + "." + training_file[-2] + training_file[-1]
    f = open(model_name, "w")
    for c1 in vocabulary:
        for c2 in vocabulary:
            for c3 in vocabulary:
                if tri_counts[c1+c2+c3] + alpha == 0:
                    prob = 0
                else:
                    prob = (tri_counts[c1+c2+c3] + alpha)/(bi_counts[c1+c2] + alpha*len(vocabulary))   # P(c1+c2+c3 | c1+c2)
                f.write(c1+c2+c3 + '\t' + str(prob) + '\n')
    f.close()
    return model_name
    
    

def cross_entropy(model_name, test_name):
    """
    - model_name is a path to a file representing a trigram language model.
    - test_name is a path to a text file used as a test set.
    Returns the model cross-entropy based on the test set. If the cross-entropy is infinity, returns -1.
    """
    log2prob = 0.0
    n = 0.0
    with open(model_name) as model_file:
        model = load_model(model_file)
        with open(test_name) as test:
            for line in test:
                line = preprocess_line(line)
                for i in range(len(line)-2):
                    if model[line[i:i+3]] == 0: return -1
                    log2prob += log(model[line[i:i+3]], 2)
                n += len(line)-2
    return -1.0/n * log2prob

def cross_entropy_from_alpha(train, test, alpha, model_name):
    """
    - train is a path to a text file used as a training set
    - test is a path to a text file used as a test set
    - alpha is a non-negative value used for aplha-smoothing
    - model_name is a string
    It creates a model (stored under the name model_name) based on the training set using
    MLE with alpha-smoothing. Returns the cross-entropy of the model based on the training set.
    """
    model_name = create_model(train, model_name, alpha)
    return cross_entropy(model_name, test)

idioma = ""

def plot_cross_entropy_alpha(alpha_lower, alpha_upper, samples, train, validation):
    """
    - 0 <= alpha_lower <= alpha_upper. [alpha_lower, alpha_upper]
    - samples is a positive integer indicating the number of samples in the plot
    - train is a path to a text file used as a training set
    - validation is a path to a text file used as a validation set
    It shows a plot with the cross-entropy of some models with different alphas used in the alpha-smoothing.
    The models are generated using the training set and the cross-entropy is calculated using the validation set.
    """
    for i in range(samples) :
        alpha = alpha_lower + i*(alpha_upper-alpha_lower)/(samples-1)
        entro = cross_entropy_from_alpha(train, validation, alpha, "validation_model")
        if entro!=-1 :
            plt.plot(alpha, entro, marker='o', color='blue')
    plt.xlabel('alpha')
    plt.ylabel('cross entropy')
    plt.title("Cross-entropy given alpha in the German set.")
    plt.show()

def perplexity(model_name, test_name):
    """
    - model_name is a path to a file representing a trigram language model.
    - test_name is a path to a text file used as a test set.
    Returns the model perplexity based on the test set. If the cross-entropy is infinity, returns -1.
    """
    return 2**cross_entropy(model_name, test_name)

def plot_perplexities(test_name):
    """
    - test_name is a path to a text file used as a test set.
    It shows a bar plot with the perplexity for each model previously created (english, spanish and german) using the test text.
    """
    perplex_en = 2**cross_entropy('model.en', test_name)
    perplex_es = 2**cross_entropy('model.es', test_name)
    perplex_de = 2**cross_entropy('model.de', test_name)
    plt.title('Perplexity of a test document using different models')
    plt.xlabel('Model used')
    plt.ylabel('Perplexity on the test text')
    plt.bar([0,1,2],[perplex_en, perplex_es, perplex_de], tick_label=['model.en', 'model.es', 'model.de'])
    

if __name__ == '__main__':
    generate_from_LM('model.es')
