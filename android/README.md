This is still work in progress, more to come

## TODO

   * Optimize graph construction, current one is below accuracy

   * Load model from the AAR (mmap them in tflite style)

   * Add decoding speed measurement

   * Add wakeup word

   * Add speakerid

   * Integrate proper hardware optimized neural network library. Candidates are:

      * https://github.com/XiaoMi/mace
      * https://github.com/Tencent/ncnn
      * https://developer.android.com/ndk/guides/neuralnetworks/ (since API level 27)
      * https://github.com/google/XNNPACK

   * Quantization for the models
