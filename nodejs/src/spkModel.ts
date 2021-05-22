import lib, { VoskSpkModel } from './lib'

/**
 * Build a Speaker Model from a speaker model file.
 * The Speaker Model enables speaker identification.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
class SpkModel {
  protected handle: VoskSpkModel

  /**
   * Loads speaker model data from the file and returns the model object
   *
   * @param {string} modelPath the path of the model on the filesystem
   * @see models [models](https://alphacephei.com/vosk/models)
   */
  constructor(modelPath: string) {
    this.handle = lib.vosk_spk_model_new(modelPath)
  }

  /**
   * Releases the model memory
   *
   * The model object is reference-counted so if some recognizer
   * depends on this model, model might still stay alive. When
   * last recognizer is released, model will be released too.
   */
  free() {
    lib.vosk_spk_model_free(this.handle)
  }

  getHandle() {
    return this.handle
  }
}

export default SpkModel
