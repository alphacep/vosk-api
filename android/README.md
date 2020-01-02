This is still work in progress, more to come

## TODO

   * Integrate https://github.com/jcsilva/docker-kaldi-android build scripts and make sure it builds
     for all architectures (x86, armv7, arm64). Think of moving Kaldi build to cmake for quick portability.

   * Build proper optimized large vocabulary model (maybe 20k words from teldium, 4-5 layers, small enough to run on mobile)

   * Move to grammar decoder to avoid huge HCLG model. https://github.com/jpuigcerver/kaldi-decoders

   * Load model from the AAR (mmap them in tflite style)

   * Add decoding speed measurement

   * Add wakeup word

   * Integrate proper hardware optimized neural network library. Candidates are:

      * https://github.com/XiaoMi/mace
      * https://github.com/Tencent/ncnn
      * https://developer.android.com/ndk/guides/neuralnetworks/ (since API level 27)
      * https://github.com/google/XNNPACK

   * Quantization for the models
