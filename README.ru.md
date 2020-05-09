[![Build Status](https://travis-ci.com/alphacep/vosk-api.svg?branch=master)](https://travis-ci.com/alphacep/vosk-api)

[EN](README.md)

[中文](README.zh.md)

Библитека для распознавания речи "Воск". Преимущества библиотеки:

  1. Поддерживает 9 языков - русский, английский, немецкий, французский, португальский, испанский, китайский, турецкий, вьетнамский. В скором времени будут добавлены и другие
  1. Работает без доступа к сети даже на мобильных устройствах - Raspberry Pi, Android, iOS
  1. Устанавливается с помощью простой команды `pip3 install vosk` без дополнительных шагов
  1. Модели для каждого языка занимают всего 50Мб, но есть и гораздо более точные большие модели для более точного распознавания
  1. Сделана для потоковой обработки звука, что позволяет реализовать мгновенную реакцию на команды
  1. Поддерживает несколько популярных языков программирования - Java, C#, Javascript
  1. Позволяет быстро настраивать словарь распознавания для улучшения точности распознавания
  1. Позволяет идентифицировать говорящего

## Сборка для Android

```
cd android
gradle build
```

Сборка включает платформы x86, armv7, arm64

Для примера приложения, созданного с помощью библиотеки "Воск" смотрите [демо проект](https://github.com/alphacep/kaldi-android-demo).

## Сборка для iOS

Доступна позапросу. Напишите нам [contact@alphacephei.com](mailto:contact@alphacephei.com).

## Установка в Python через Pypi

Проще всего установить "Воск" с помощью pip. Собирать ничего не нужно.

На настоящий момент мы поддерживаем следующие платформы:

  * Linux on x86_64
  * Raspbian on Raspberry Pi
  * Linux on arm64
  * OSX
  * Windows

Для начала убедитесь, что используются достаточно новые версии pip и Python:

  * Python версии: 3.5-3.8 (Linux), 3.6-3.7 (ARM), 3.8 (OSX), 3.8 (Windows)
  * pip версии: 19.0 и новее

Обновите Python и Pip если нужно, а затем установите "Воск" такой командой:

```
pip3 install vosk
```

Для использования "Воск" смотрите примеры ниже.

Учтите, что некоторые платформы не поддерживаютя pip, например arm64. В этом случае можно установить пакет с github:

```
pip3 install https://github.com/alphacep/vosk-api/releases/download/0.3.7/vosk-0.3.7-cp37-cp37m-linux_aarch64.whl
```

Также учтите, что некотрые сборки требуют наличия libgfortran. Например, на RPi необходимо установить libgfortran с 
помощью менеджера пакетов.

В случае проблем с установкой, проверьте вывод следующих команд:

  * python3 --version
  * pip3 --version
  * pip3 -v install vosk

## Сервер для протоколов Websocket и GRPC

Мы также разработали сервер для приложений, требующих обработки больших объёмов с большой точностью, например, для телефонии.

Сервер устанавливается одной командой с помощью docker:

```
docker run -d -p 2700:2700 alphacep/kaldi-en:latest
```

Смотрите проект https://github.com/alphacep/vosk-server


## Сборка из исходников

Если нужно собрать проект из исходного кода, необходимо будет собрать 
Kaldi самостоятельно. Сборка досаточно простая и прямолинейная, но может
быть непривычной для начинающих. Обращайте внимания на сообщения об ошибках
в процессе сборки.

#### Сборка Kaldi для модулей на Python, Java, C# на Linux

```
git clone https://github.com/kaldi-asr/kaldi
cd kaldi/tools
make
```

установите все рекомандуемые пакеты и повторите `make` если потребуется.

```
extras/install_openblas.sh
cd ../src
./configure --mathlib=OPENBLAS --shared --use-cuda=no
make -j 10
```

#### Kaldi compilation on OSX

Процесс сборки почти такой же, как и на Linux, но нужно учесть что Kaldi в OSX использует Accelerate вместо OpenBlas

#### Сборка модуля на Python

После Kaldi можно собрать модуль Python

```
export KALDI_ROOT=<KALDI_ROOT>
cd python
python3 setup.py install
```

#### Запуск примера для Python

Выполните следующие команды:

```
cd vosk-api/python/example
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.3.zip
unzip alphacep-model-android-en-us-0.3.zip
mv alphacep-model-android-en-us-0.3 model-en
python3 ./test_simple.py test.wav
```

Для того, чтобы распознавать другой файл, переведите его в нужный формат - PCM 16кГц 16бит 1канал. Это можно сделать с помощью ffmpeg.

Другие примеры, в том числе использования микрофона, распознавание с небольшим словарём и распознавание говорящего можно найти в [каталоге python/example](https://github.com/alphacep/vosk-api/tree/master/python/example)

#### Сборка для Java

Перейдите в каталог Java и запустите сборку

```
cd java && KALDI_ROOT=<KALDI_ROOT> make
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.3.zip
unzip alphacep-model-android-en-us-0.3.zip
mv alphacep-model-android-en-us-0.3 model
make run
```

#### Сборка для C#

Для сборки в среде Mono.

```
cd csharp && KALDI_ROOT=<KALDI_ROOT> make
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.3.zip
unzip alphacep-model-android-en-us-0.3.zip
mv alphacep-model-android-en-us-0.3 model
mono test.exe
```

.NET тоже должен работать, хотя мы не пробовали.

## Модели для разных языков

По информации о моделях смотрите соответствующую [страницу документации](https://github.com/alphacep/vosk-api/blob/master/doc/models.md).

## Contact Us

Если возникли вопросы, свяжитесь с нами:

   * Создайте проблему тут на github
   * Напишите нам по почте [contact@alphacephei.com](mailto:contact@alphacephei.com)
   * Заходите в нашу группу в Телеграмме [@speech_recognition_ru](https://t.me/speech_recognition_ru)
