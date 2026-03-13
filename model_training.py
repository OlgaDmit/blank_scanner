import keras
from keras.datasets import mnist
from keras.models import Sequential
#from keras.layers import Dense, Dropout, Flatten
#from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
import os
import numpy as np
from PIL import Image
import cv2
from tensorflow.keras.optimizers import SGD
from albumentations import (
    Compose, Rotate, ShiftScaleRotate, RandomScale, 
    RandomBrightnessContrast, HorizontalFlip, VerticalFlip
)
from preprocessing import preprocess_one_digit_area


#from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam

# Загрузка данных MNIST
(x_train, y_train), (x_test, y_test) = mnist.load_data()

augmentations = Compose([
    Rotate(limit=15, p=0.5),  # случайный поворот до 15 градусов
    RandomScale(scale_limit=0.2, p=0.5),
])

for index in range(len(x_train)):
    augmented = augmentations(image=x_train[index])["image"]
    x_train[index] = preprocess_one_digit_area(augmented, 28, 28, invert = False)

for index in range(len(x_test)):
    augmented = augmentations(image=x_test[index])["image"]
    x_test[index] = preprocess_one_digit_area(augmented, 28, 28, invert = False)


# Загрузка изображений запятых
def load_commas(folder, num_samples, target_class, inv):
    images = []
    labels = []
    if inv:
        files = os.listdir(folder)[-num_samples:]  # Берем только последние num_samples изображений
    else:
        files = os.listdir(folder)[:num_samples]  # Берем только первые num_samples изображений
    for file in files:
        img_path = os.path.join(folder, file)
        img = Image.open(img_path).convert('L')  # Конвертируем в grayscale
        img = img.resize((28, 28))  # Масштабируем до 28x28 как в MNIST 
        img_array = np.array(img)
#        img_array = cv2.bitwise_not(img_array) # Инвертируем
        images.append(img_array)
        labels.append(target_class)
    return np.array(images), np.array(labels)

# Загружаем запятые (предположим, что класс запятых - 10)
#commas_train, commas_train_labels = load_commas('commas/train', 3000, 10)  # Пример: 1000 тренировочных запятых
#commas_test, commas_test_labels = load_commas('commas/test', 200, 10)     # Пример: 200 тестовых запятых

commas_train, commas_train_labels = load_commas('commas_new_6400/', 6000, 10, 0)  # Пример: 1000 тренировочных запятых
commas_test, commas_test_labels = load_commas('commas_new_6400/', 832, 10, 1)     # Пример: 200 тестовых запятых

# Объединяем с MNIST данными
x_train = np.concatenate((x_train, commas_train))
y_train = np.concatenate((y_train, commas_train_labels))
x_test = np.concatenate((x_test, commas_test))
y_test = np.concatenate((y_test, commas_test_labels))

#num_classes = 10
num_classes = 11  # Теперь у нас 11 классов (10 цифр + запятые)

# Решейп и нормализация
x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)
x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
input_shape = (28, 28, 1)
#print(x_train)

# Преобразование векторных классов в бинарные матрицы
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255

print('Размерность x_train:', x_train.shape)
print(x_train.shape[0], 'Размер train')
print(x_test.shape[0], 'Размер test')







batch_size = 32 #32 #

epochs = 10

#model = Sequential()
#model.add(Conv2D(32, kernel_size=(3, 3),activation='relu',input_shape=input_shape))
#model.add(Conv2D(64, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.25))
#model.add(Flatten())
#model.add(Dense(256, activation='relu'))
#model.add(Dropout(0.5))
#model.add(Dense(num_classes, activation='softmax'))
#model.compile(loss=keras.losses.categorical_crossentropy,optimizer=keras.optimizers.Adadelta(),metrics=['accuracy'])

#model = Sequential()
#model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
#model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
#model.add(MaxPooling2D((2, 2)))
#model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
#model.add(MaxPooling2D((2, 2)))
#model.add(Flatten())
#model.add(Dense(10 * num_classes, activation='relu', kernel_initializer='he_uniform'))
#model.add(Dense(num_classes, activation='softmax'))
## compile model
#opt = SGD(learning_rate=0.01, momentum=0.9)
#model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

#model = Sequential()
#model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
#model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
#model.add(Dropout(0.2))
#model.add(MaxPooling2D((2, 2)))
##model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
#model.add(Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_uniform'))
#model.add(MaxPooling2D((2, 2)))
##model.add(MaxPooling2D((2, 2)))
#model.add(Dropout(0.3))
#model.add(Flatten())
#model.add(Dense(num_classes**2, activation='relu', kernel_initializer='he_uniform'))
#model.add(Dropout(0.4))
#model.add(Dense(num_classes, activation='softmax'))
## compile model
#opt = SGD(learning_rate=0.01, momentum=0.9)
#model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

#model = Sequential()
#model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
#model.add(Conv2D(63, (3,3), activation='relu', kernel_initializer='he_uniform'))
#model.add(Dropout(0.2))
#model.add(MaxPooling2D((2, 2)))
##model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
#model.add(Conv2D(128, (5,5), activation='relu', kernel_initializer='he_uniform'))
#model.add(Dropout(0.3))
#model.add(MaxPooling2D((2, 2)))
##model.add(MaxPooling2D((2, 2)))
#model.add(Flatten())
#model.add(Dense(num_classes**2, activation='relu', kernel_initializer='he_uniform'))
#model.add(Dropout(0.4))
#model.add(Dense(num_classes, activation='softmax'))
## compile model
#opt = SGD(learning_rate=0.01, momentum=0.9)
#model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])



#model = Sequential()
#
## Первый блок (захват вертикальных и горизонтальных признаков)
#model.add(Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=(28, 28, 1)))
#model.add(BatchNormalization())  # ускоряет обучение и стабилизирует его
#model.add(MaxPooling2D((2, 2)))
#model.add(Dropout(0.15))  # уменьшаем переобучение
#
#model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
#model.add(BatchNormalization())
#model.add(MaxPooling2D((2, 2)))
#model.add(Dropout(0.2))  # уменьшаем переобучение
#
## Второй блок (увеличение глубины признаков)
#model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
#model.add(BatchNormalization())
#model.add(MaxPooling2D((2, 2)))
#model.add(Dropout(0.2))
#
## Третий блок (используем вертикальные фильтры для вытянутых цифр)
#model.add(Conv2D(128, (5, 5), activation='relu', padding='same'))  # вертикальный фильтр (3x5)
#model.add(BatchNormalization())
#model.add(MaxPooling2D((2, 2)))
#model.add(Dropout(0.3))
#
## Полносвязные слои
#model.add(Flatten())
#model.add(Dense(num_classes**2, activation='relu'))
#model.add(BatchNormalization())
#model.add(Dropout(0.4))
#model.add(Dense(num_classes, activation='softmax'))
#
## Компиляция с Adam (лучше, чем SGD для MNIST)
#opt = Adam(learning_rate=0.001)
#model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])


model = Sequential()
model.add(Conv2D(32, kernel_size=(3, 3),activation='relu',input_shape=input_shape))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(num_classes**2, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))
model.compile(loss=keras.losses.categorical_crossentropy,optimizer=keras.optimizers.Adadelta(),metrics=['accuracy'])

model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
model.add(MaxPooling2D((2, 2)))
model.add(Dropout(0.25))
model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform'))
model.add(MaxPooling2D((2, 2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(10 * num_classes, activation='relu', kernel_initializer='he_uniform'))
model.add(Dropout(0.5))
model.add(Dense(num_classes, activation='softmax'))
# compile model
opt = SGD(learning_rate=0.01, momentum=0.9)
model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])



hist = model.fit(x_train, y_train, batch_size = batch_size, epochs=epochs, verbose=1, validation_data=(x_test, y_test))
print("Модель успешно обучена")

model.save('model/mnist_new.h5')
print("Модель сохранена как mnist.h5")


score = model.evaluate(x_test, y_test, verbose=0)
print('Потери на тесте:', score[0])
print('Точность на тесте:', score[1])