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
   *
   * @throws If the speaker model could not be created
   */
  constructor(modelPath: string)
  constructor(handle: VoskSpkModel)

  constructor(modelPathOrHandle: string | VoskSpkModel) {
    if (typeof modelPathOrHandle !== 'string') {
      this.handle = modelPathOrHandle
      return
    }
    const handle = lib.vosk_spk_model_new(modelPathOrHandle)
    if (!handle) {
      throw new Error('Failed to create a speaker model')
    }
    this.handle = handle
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

export const getSpkModelAsync = (modelPath: string) =>
  new Promise<SpkModel>((res, rej) => {
    lib.vosk_spk_model_new.async(modelPath, (err, handle) => {
      if (err) {
        rej(err)
        return
      }
      if (!handle) {
        rej('Failed to create a speaker model')
        return
      }
      const spkModel = new SpkModel(handle)
      res(spkModel)
    })
  })

export default SpkModel
