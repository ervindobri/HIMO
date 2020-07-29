from __future__ import print_function

import queue
from collections import deque
from threading import Lock, Thread
import matplotlib

import matplotlib.pyplot as plt

import numpy as np
# np.random.seed(1)
import tensorflow as tf
from kivy.clock import Clock
from tensorflow import keras
from keras import regularizers
from keras.models import load_model
from sklearn import preprocessing
import myo
import time
import sys
import psutil
import os

# New Imports
import datetime as dt
import warnings
import pickle
import json

# This training set will contain 1000 samples of 8 sensor values
from tensorflow.python.keras import callbacks
from tensorflow.python.keras.callbacks import Callback

global training_set
global number_of_samples
global index_training_set, middle_training_set, thumb_training_set, verification_set
global data_array
matplotlib.use("TkAgg")

# number_of_gestures = 3
number_of_gestures = 3
number_of_samples = 1000
data_array = []

# region VARIABLES
# 8 Sensors in armband
Sensor1 = np.zeros((1, number_of_samples))
Sensor2 = np.zeros((1, number_of_samples))
Sensor3 = np.zeros((1, number_of_samples))
Sensor4 = np.zeros((1, number_of_samples))
Sensor5 = np.zeros((1, number_of_samples))
Sensor6 = np.zeros((1, number_of_samples))
Sensor7 = np.zeros((1, number_of_samples))
Sensor8 = np.zeros((1, number_of_samples))

# TODO: name gestures
# FOOT GESTURES: tiptoe, heel, toe crunches
tiptoe_training_set = np.zeros((8, number_of_samples))
toe_crunches_training_set = np.zeros((8, number_of_samples))
rest_training_set = np.zeros((8, number_of_samples))

validation_set = np.zeros((8, number_of_samples))
training_set = np.zeros((8, number_of_samples))

tiptoe_label = 0
toe_crunches_label = 1
rest_label = 1


result_path = 'X:\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\data\\results\\'
# global result
myo.init('X:\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\myo64.dll')

# Custom variables
instructions = ""
epoch_counter = 0
max_epochs = 300
session_finished = False

# endregion

# region FUNCTIONS

# TODO: declare and define used functions
# Check if Myo Connect.exe process is running
def check_if_process_running(procname):
    try:
        for proc in psutil.process_iter():
            if proc.name() == 'Myo Connect.exe':
                return True

        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        print(procname, " not running")


# Restart myo connect.exe process if its not running
def restart_process():
    global instructions
    procname = "Myo Connect.exe"

    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == procname:
            proc.kill()
            # Wait a second
            time.sleep(1)

    while not check_if_process_running(procname):
        path = 'C:\Program Files (x86)\Thalmic Labs\Myo Connect\Myo Connect.exe'
        os.startfile(path)
        time.sleep(1)
        # while(check_if_process_running()==False):
        #    pass

    print("MYO Process started")
    instructions = "MYO App started"
    return True


# TODO: save training and test data separately by gestures

# This class from Myo-python SDK listens to EMG signals from armband
class Listener(myo.DeviceListener):

    def __init__(self, n):
        self.n = n
        self.lock = Lock()
        self.emg_data_queue = deque(maxlen=n)

    def on_connected(self, event):
        print("Myo Connected")
        self.started = time.time()
        event.device.stream_emg(True)

    def get_emg_data(self):
        with self.lock:
            print("H")  # Ignore this

    def on_emg(self, event):
        with self.lock:
            self.emg_data_queue.append(event.emg)

            if len(list(self.emg_data_queue)) >= number_of_samples:
                data_array.append(list(self.emg_data_queue))
                self.emg_data_queue.clear()
                return False


# This function plots results for validation and training data for a certain subject
def DisplayResults(subjectname):
    try:
        filepath = 'X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results/dump/' + subjectname + '-dump.dmp'
        # print(filepath)
        history = pickle.load(open(filepath, "rb"))
        print("Model load successful")
        # print(history)
    except:
        print("No such model exists! Please try again.")
        return

    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    # Here we display the training and test loss for model
    ax1.plot(history['accuracy'])
    ax1.plot(history['val_accuracy'])
    ax1.set_title('model accuracy')
    ax1.set_ylim((0, 1.05))
    # ax1.c('accuracy')
    ax1.set_xlabel('epoch')
    ax1.legend(['train', 'test'], loc='lower right')
    # ax1.show()
    # summarize history for loss
    ax2.plot(history['loss'])
    ax2.plot(history['val_loss'])
    ax2.set_title('model loss')
    ax2.set_xlabel('loss')
    ax2.set_xlabel('epoch')
    ax2.legend(['train', 'test'], loc='upper right')
    # print(result_path + str(dt.datetime.now()) + '-' + name + '-result')
    # fig = plt.gcf()
    try:
        save_file = (dt.datetime.now()).strftime("%Y-%m-%d-%H+%M+%S") + '=' + subjectname + '=result.png'
        plt.savefig(result_path + '/figures/' + save_file, bbox_inches='tight')
        print(save_file + " :figure saved successfully!")
        return result_path + '/figures/' + save_file
        # Plot after saving to avoid a weird tkinter exception
        # plt.show(block=False)
        # plt.close()
    except:
        pass


# Method for predicting new gestures until break key is pressed
# TODO: Save predicted results for later
def PredictGestures(subjectname, q, *largs):
    global number_of_samples
    # global result
    averages = number_of_samples / 50
    # Initializing array for verification_averages
    validation_averages = np.zeros((int(averages), 8))
    model = load_model(result_path + subjectname + '_realistic_model.h5')
    # enter = ''

    result = ''
    hub = myo.Hub()
    number_of_samples = 100
    listener = Listener(number_of_samples)

    # while not session_finished:
    try:
        print("Show a foot gesture and press ENTER to get its classification!")
        hub.run(listener.on_event, 10000)
        # Here we send the received number of samples making them a list of 1000 rows 8 columns
        validation_set = np.array((data_array[0]))
        data_array.clear()
    except:
        while not restart_process():
            pass
        # Wait for 3 seconds until Myo Connect.exe starts
        time.sleep(3)

    validation_set = np.absolute(validation_set)
    div = 50
    # We add one because iterator below starts from 1
    batches = int(number_of_samples / div) + 1
    for i in range(1, batches):
        validation_averages[i - 1, :] = np.mean(validation_set[(i - 1) * div:i * div, :], axis=0)

    validation_data = validation_averages
    # print("Verification matrix shape is ", validation_data.shape)

    predictions = model.predict(validation_data, batch_size=16)
    predicted_value = np.argmax(predictions[0])
    if predicted_value == 0:
        print("Tiptoe stand")
        result = "TIP TOE"
        q.put(result)
    elif predicted_value == 1:
        print("Toe Crunches ")
        result = "TOE CRUNCH"
        q.put(result)
    else:
        print("Rest gesture")
        result = ''
        q.put(result)


# This method is responsible for training EMG data
def TrainEMG(conc_array, name, q):
    global training_set
    global tiptoe_training_set, toe_crunches_training_set
    # global heel_training_set

    global number_of_samples
    validation_set = np.zeros((8, number_of_samples))
    labels = []
    global instructions
    global epoch_counter
    epoch_counter = 0
    print("Preprocess EMG data")
    instructions = "Preprocess EMG data"
    # This division is to make the iterator for making labels run 20 times in inner loop and 3 times in outer loop
    # running total 60 times for 3 foot gestures
    samples = conc_array.shape[0] / number_of_gestures
    # Now we append all data in training label
    # We iterate to make 3 finger movement labels.
    for i in range(0, number_of_gestures):
        for j in range(0, int(samples)):
            labels.append(i)
    labels = np.asarray(labels)
    # print(labels, len(labels), type(labels))
    # print(conc_array.shape[0])

    permutation_function = np.random.permutation(conc_array.shape[0])
    total_samples = conc_array.shape[0]
    all_shuffled_data, all_shuffled_labels = np.zeros((total_samples, 8)), np.zeros((total_samples, 8))

    all_shuffled_data, all_shuffled_labels = conc_array[permutation_function], labels[permutation_function]
    # print(all_shuffled_data.shape)
    # print(all_shuffled_labels.shape)

    number_of_training_samples = np.int(np.floor(0.8 * total_samples))
    train_data = np.zeros((number_of_training_samples, 8))
    train_labels = np.zeros((number_of_training_samples, 8))
    # print("TS ", number_of_training_samples, " S ", number_of_samples)
    number_of_validation_samples = np.int(total_samples - number_of_training_samples)
    train_data = all_shuffled_data[0:number_of_training_samples, :]
    train_labels = all_shuffled_labels[0:number_of_training_samples, ]
    # print("Length of train data is ", train_data.shape)
    validation_data = all_shuffled_data[number_of_training_samples:total_samples, :]
    validation_labels = all_shuffled_labels[number_of_training_samples:total_samples, ]
    # print("Length of validation data is ", validation_data.shape, " validation labels is ", validation_labels.shape)
    # print(train_data, train_labels)

    print("Building model...")
    instructions = "Building model..."
    model = keras.Sequential([
        # Input dimensions means input columns. Here we have 8 columns, one for each sensor
        keras.layers.Dense(8, activation=tf.nn.relu, input_dim=8, kernel_regularizer=regularizers.l2(0.1)),
        keras.layers.BatchNormalization(),
        keras.layers.Dense(number_of_gestures, activation=tf.nn.softmax)])

    adam_optimizer = keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    model.compile(optimizer=adam_optimizer,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    print("Fitting training data to the model...")
    instructions = "Fitting training data to the model..."
    history = model.fit(train_data, train_labels, epochs=300, validation_data=(validation_data, validation_labels),
                        batch_size=16, verbose=0, callbacks=[CustomCallback()])

    print("Saving model for later...")
    save_path = result_path + name + '_realistic_model.h5'
    model.save(save_path)
    instructions = "Saving model for later..."
    # print(history)
    # Save model history into dump file
    filepath = 'X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results/dump/' + name + '-dump.dmp'
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as file_pi:
        pickle.dump(history.history, file_pi)


    instructions = "Training model successful!"

    #Save plot
    save_file = DisplayResults(name)
    q.put(save_file)
    return "RE-TRAIN SUCCESSFUL"

class CustomCallback(keras.callbacks.Callback):

    def on_epoch_begin(self, epoch, logs=None):
        # keys = list(logs.keys())
        # print("Start epoch {} of training; got log keys: {}".format(epoch, keys))
        # print("Start epoch {} of training; counter: {}".format(epoch, epoch_counter))
        pass

    def on_epoch_end(self, epoch, logs=None):
        global epoch_counter
        # keys = list(logs.keys())
        epoch_counter = epoch + 1
        # print("End epoch {} of training; got log keys: {}".format(epoch, epoch_counter))



def PrepareTrainingData(name, q):
    # import queue
    global instructions
    tiptoe_training_set = np.zeros((8, number_of_samples))
    toe_crunches_training_set = np.zeros((8, number_of_samples))
    rest_training_set = np.zeros((8, number_of_samples))

    validation_set = np.zeros((8, number_of_samples))
    training_set = np.zeros((8, number_of_samples))
    # This function kills Myo Connect.exe and restarts it to make sure it is running
    # Because sometimes the application does not run even when Myo Connect process is running
    # So i think its a good idea to just kill if its not running and restart it

    while not restart_process():
        pass
    # Wait for 3 seconds until Myo Connect.exe starts
    # time.sleep(3)

    # Initialize the SDK of Myo Armband
    myo.init('X:\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\myo64.dll')
    hub = myo.Hub()
    listener = Listener(number_of_samples)

    # region TIPTOE_DATA
    instructions = "Stand on your toes!"
    print(instructions)
    time.sleep(0.5)
    while True:
        try:
            hub = myo.Hub()
            listener = Listener(number_of_samples)
            # input("Stand on your toes!")
            hub.run(listener.on_event, 10000)
            tiptoe_training_set = np.array((data_array[0]))
            data_array.clear()
            break
        except:
            while not restart_process():
                pass
            # Wait for 3 seconds until Myo Connect.exe starts
            time.sleep(3)

    # Here we send the received number of samples making them a list of 1000 rows 8 columns
    # just how we need to feed to tensorflow
    # endregion
    # region TOE_CRUNCH_DATA
    instructions = "Tip toe data ready!"
    print(instructions)

    time.sleep(1)
    instructions = "Crunch your toes!"

    print(instructions)
    time.sleep(1)
    while True:
        try:
            hub = myo.Hub()
            listener = Listener(number_of_samples)
            # input("Crunch your toes!")
            hub.run(listener.on_event, 10000)
            toe_crunches_training_set = np.array((data_array[0]))
            data_array.clear()
            break
        except:
            while not restart_process():
                pass
            # Wait for 3 seconds until Myo Connect.exe starts
            time.sleep(3)

    instructions = "Toe crunch data ready!"
    print(instructions)

    time.sleep(1)

    # endregion
    # region REST_DATA
    time.sleep(1)
    instructions = "Rest your foot!"

    print(instructions)
    time.sleep(1)
    while True:
        try:
            hub = myo.Hub()
            listener = Listener(number_of_samples)
            hub.run(listener.on_event, 10000)
            rest_training_set = np.array((data_array[0]))
            data_array.clear()
            break
        except:
            while not restart_process():
                pass
            # Wait for 3 seconds until Myo Connect.exe starts
            time.sleep(3)

    instructions = "Rest data ready!"
    print(instructions)

    time.sleep(1)

    # endregion

    # region POSTPROCESS_DATA
    # Absolutes of foot gesture data
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        tiptoe_training_set = np.absolute(tiptoe_training_set)
        toe_crunches_training_set = np.absolute(toe_crunches_training_set)
        rest_training_set = np.absolute(rest_training_set)

        div = 50
        averages = int(number_of_samples / div)
        tiptoe_averages = np.zeros((int(averages), 8))
        toe_crunches_averages = np.zeros((int(averages), 8))
        rest_averages = np.zeros((int(averages), 8))

        # Here we are calculating the mean values of all finger open data set and storing them as n/50 samples
        # because 50 batches of n samples is equal to n/50 averages
        for i in range(1, averages + 1):
            tiptoe_averages[i - 1, :] = np.mean(tiptoe_training_set[(i - 1) * div:i * div, :], axis=0)
            toe_crunches_averages[i - 1, :] = np.mean(toe_crunches_training_set[(i - 1) * div:i * div, :], axis=0)
            rest_averages[i - 1, :] = np.mean(rest_training_set[(i - 1) * div:i * div, :], axis=0)

        # Here we stack all the data row wise
        # conc_array = np.concatenate([tiptoe_averages, heel_averages, toe_crunches_averages], axis=0)
        conc_array = np.concatenate([tiptoe_averages, toe_crunches_averages, rest_averages], axis=0)
    try:
        np.savetxt(result_path + name + '.txt', conc_array, fmt='%i')
        print("Saving training data successful!")
        instructions = "Saving training data successful!"

        result = conc_array
        q.put(result)
    except:
        print("Saving training data failed!")
        instructions = "Saving training data failed!"

        pass
    # endregion


# endregion
if __name__ == '__main__':
    # Initialize data container for each gesture
    # input()
    # name = input("Enter name of Subject")
    # Initialize the SDK of Myo Armband
    # myo.init('X:\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\myo64.dll')

    # TODO: NOPE y/n question(prompt) if wants to train, or display results and predict new data
    # Preparing new training data
    # conc_array = PrepareTrainingData(name)
    # In this method the EMG data gets trained and validated
    # TrainEMG(conc_array, name)


    # Train existing data
    # name = 'teszt'
    # data = np.loadtxt(result_path + name + '.txt')
    # TrainEMG(data, name)

    # Predicting new gestures, based on subjects model
    # PredictGestures('teszt')
    # Display existing training results
    # DisplayResults(name)

    # Prdicting gestures for Ervin-lab1
    # PredictGestures(name)


    # DEBUG

    # region PREDICT_CONSTANTLY
    hub = myo.Hub()
    number_of_samples = 100
    listener = Listener(number_of_samples)
    counter = 0
    q = queue.Queue()
    averages = number_of_samples / 50
    # # Initializing array for verification_averages
    validation_averages = np.zeros((int(averages), 8))
    model = load_model(result_path + 'Ervin' + '_realistic_model.h5')


    while counter < 5:
        PredictGestures('Ervin', q)
        counter+=1

    # endregion

    # while hub.run(listener.on_event, 1000):
    #     print(data_array)
    #     pass
        # counter+=1
        # print(len(data_array[0]))
        # if len(data_array):
            # print(data_array[0])
        # data_array.clear()
        # print(data_array)
        # print(hub.running)
        # try:
        #
        #     print("Show a foot gesture and press ENTER to get its classification!")
        #     # Here we send the received number of samples making them a list of 1000 rows 8 columns
        #     validation_set = np.array((data_array[0]))
        #     data_array.clear()
        # except:
        #     while not restart_process():
        #         pass
        #     # Wait for 3 seconds until Myo Connect.exe starts
        #     time.sleep(3)
        #
        # validation_set = np.absolute(validation_set)
        # div = 50
        # # We add one because iterator below starts from 1
        # batches = int(number_of_samples / div) + 1
        # for i in range(1, batches):
        #     validation_averages[i - 1, :] = np.mean(validation_set[(i - 1) * div:i * div, :], axis=0)
        #
        # validation_data = validation_averages
        # # print("Verification matrix shape is ", validation_data.shape)
        #
        # predictions = model.predict(validation_data, batch_size=16)
        # predicted_value = np.argmax(predictions[0])
        # if predicted_value == 0:
        #     print("Tiptoe stand")
        #     result = "TIP TOE"
        #     q.put(result)
        # elif predicted_value == 1:
        #     print("Toe Crunches ")
        #     result = "TOE CRUNCH"
        #     q.put(result)
        # else:
        #     print("Rest gesture")
        #     result = ''
        #     q.put(result)









    # region PREPARE AND TRAIN
    # q = queue.Queue()
    # PrepareTrainingData('teszt', q)
    # res = q.get()
    # # print(res)
    #
    #
    # data = np.loadtxt(result_path + 'teszt' + '.txt')
    # TrainEMG(data, 'teszt', q)

    # endregion
    pass
