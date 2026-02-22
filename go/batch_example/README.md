This example expects a `s16le` converted audio file and converts it to text in a
manner that imitates the Python example of [test_gpu_batch.py](../python/example/test_gpu_batch.py).

Note that the `libvosk.so` must be in the library path. This was successfully tested on
Ubuntu 24.04 with Go 1.18, gcc-11, NVIDIA driver 570.172.08.
