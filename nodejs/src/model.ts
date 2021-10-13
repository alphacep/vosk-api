import lib, { VoskModel } from './lib'

/**
 * Build a Model from a model file.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
class Model {
  protected handle: VoskModel

  /**
   * Build a Model to be used with the voice recognition.
   * Each language should have it's own Model for the speech recognition to work.
   *
   * @param modelPath The abstract pathname to the model
   * @see models [models](https://alphacephei.com/vosk/models)
   *
   * @throws If the model could not be created
   */
  constructor(modelPath: string)
  constructor(handle: VoskModel)

  constructor(modelPathOrHandle: string | VoskModel) {
    if (typeof modelPathOrHandle !== 'string') {
      this.handle = modelPathOrHandle
      return
    }
    const handle = lib.vosk_model_new(modelPathOrHandle)
    if (!handle) {
      throw new Error('Failed to create a model')
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
    lib.vosk_model_free(this.handle)
  }

  getHandle() {
    return this.handle
  }
}

/**
 * Build a Model to be used with the voice recognition on a separate thread.
 * Each language should have it's own Model for the speech recognition to work.
 *
 * @param modelPath The abstract pathname to the model
 */
export const getModelAsync = (modelPath: string) =>
  new Promise<Model>((res, rej) => {
    const cb = (err: Error | null, handle: VoskModel | null) => {
      if (err) {
        rej(err)
        return
      }
      if (!handle) {
        rej('Failed to create a model')
        return
      }
      res(new Model(handle))
    }
    lib.vosk_model_new.async(modelPath, cb)
  })

export default Model
