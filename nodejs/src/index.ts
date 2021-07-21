import lib from './lib'
export { default as Model, getModelAsync } from './model'
export { default as SpkModel, getSpkModelAsync } from './spkModel'
export {
  default as Recognizer,
  WordInfo,
  PartialResult,
  Result,
  Options,
} from './recognizer'

/**
 * Set log level for Kaldi messages
 * @param level The higher, the more verbose. 0 for infos and errors. Less than 0 for silence.
 */
export const setLogLevel = (logLevel: number): void => {
  lib.vosk_set_log_level(logLevel)
}
