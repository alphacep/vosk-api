// Deno port of the vosk Node.js bindings

import path from "node:path";

// --- Type Definitions (Converted from JSDoc) ---

export interface WordResult {
  conf: number; // The confidence rate in the detection. 0 For unlikely, and 1 for totally accurate.
  start: number; // The start of the timeframe when the word is pronounced in seconds
  end: number; // The end of the timeframe when the word is pronounced in seconds
  word: string; // The word detected
}

export interface RecognitionResults {
  result?: WordResult[]; // Details about the words that have been detected (optional if words not enabled)
  text: string; // The complete sentence that have been detected
  alternatives?: RecognitionResults[]; // Present if max_alternatives > 0
}

export interface SpeakerResults {
  spk: number[]; // A floating vector representing speaker identity.
  spk_frames: number; // The number of frames used to extract speaker vector.
}

// Parameter types for Recognizer constructor
export interface BaseRecognizerParam {
  model: Model; // The language model to be used
  sampleRate: number; // The sample rate. Most models are trained at 16kHz
}

export interface GrammarRecognizerParam {
  grammar: string[]; // The list of sentences to be recognized.
}

export interface SpeakerRecognizerParam {
  speakerModel: SpeakerModel; // The SpeakerModel that will enable speaker identification
}

// Conditional result type based on Recognizer parameters
export type RecognizerResult<T> = T extends SpeakerRecognizerParam
  ? SpeakerResults & RecognitionResults
  : RecognitionResults;

export interface PartialResults {
  partial: string;
  partial_result?: WordResult[]; // If partial words are enabled
}

const __dirname = import.meta.dirname;

// --- Determine Native Library Path ---
let soname: string;
let sonameLocal: string | undefined;
const libDir = __dirname ? path.join(__dirname, "lib") : undefined;

switch (Deno.build.os) {
  case "windows": {
    // TODO: Maybe also modify PATH like the original version
    const arch = Deno.build.arch === "x86_64" ? "win-x86_64" : null;
    if (!arch) throw new Error("Unsupported Windows architecture");
    soname = "libvosk.dll";
    if (libDir) {
      sonameLocal = path.join(libDir, arch, soname);
    }
    break;
  }
  case "darwin": {
    soname = "libvosk.dylib";
    if (libDir) {
      sonameLocal = path.join(libDir, "osx-universal", soname);
    }
    break;
  }
  case "linux": {
    const arch = Deno.build.arch === "aarch64"
      ? "linux-arm64"
      : Deno.build.arch === "x86_64"
      ? "linux-x86_64"
      : null;
    if (!arch) {
      throw new Error(`Unsupported Linux architecture: ${Deno.build.arch}`);
    }
    soname = "libvosk.so";
    if (libDir) {
      sonameLocal = path.join(libDir, arch, soname);
    }
    break;
  }
  default:
    throw new Error(`Unsupported OS: ${Deno.build.os}`);
}

// --- Define FFI Symbol Signatures ---
// Note: Opaque pointers (like vosk_model*) are just 'pointer' in Deno FFI
// C strings passed *to* the library are 'buffer' (pass Uint8Array)
// C strings returned *from* the library are 'pointer' (read with UnsafePointerView)
const voskSymbols = {
  vosk_set_log_level: { parameters: ["i32"], result: "void" },
  vosk_model_new: { parameters: ["buffer"], result: "pointer" },
  vosk_model_free: { parameters: ["pointer"], result: "void" },
  vosk_spk_model_new: { parameters: ["buffer"], result: "pointer" },
  vosk_spk_model_free: { parameters: ["pointer"], result: "void" },
  vosk_recognizer_new: { parameters: ["pointer", "f32"], result: "pointer" },
  vosk_recognizer_new_spk: {
    parameters: ["pointer", "f32", "pointer"],
    result: "pointer",
  },
  vosk_recognizer_new_grm: {
    parameters: ["pointer", "f32", "buffer"], // Grammar is C string
    result: "pointer",
  },
  vosk_recognizer_free: { parameters: ["pointer"], result: "void" },
  vosk_recognizer_set_max_alternatives: {
    parameters: ["pointer", "i32"],
    result: "void",
  },
  vosk_recognizer_set_words: {
    parameters: ["pointer", "bool"],
    result: "void",
  },
  vosk_recognizer_set_partial_words: {
    parameters: ["pointer", "bool"],
    result: "void",
  },
  vosk_recognizer_set_spk_model: {
    parameters: ["pointer", "pointer"],
    result: "void",
  },
  vosk_recognizer_accept_waveform: {
    parameters: ["pointer", "buffer", "i32"], // data buffer, length
    result: "bool",
  },
  vosk_recognizer_result: { parameters: ["pointer"], result: "pointer" }, // Returns char*
  vosk_recognizer_final_result: { parameters: ["pointer"], result: "pointer" }, // Returns char*
  vosk_recognizer_partial_result: {
    parameters: ["pointer"],
    result: "pointer",
  },
  vosk_recognizer_reset: { parameters: ["pointer"], result: "void" },
} as const;

// --- Load the Native Library ---
let libvosk: Deno.DynamicLibrary<typeof voskSymbols>;
const userSetNativeLibPath = Deno.env.get("VOSK_LIB_DIR_PATH");
if (userSetNativeLibPath) {
  libvosk = Deno.dlopen(path.join(userSetNativeLibPath, soname), voskSymbols);
} else if (sonameLocal) {
  try {
    // 1. try to load local library
    libvosk = Deno.dlopen(sonameLocal, voskSymbols);
  } catch {
    try {
      // 2. try to load library installed in the system
      libvosk = Deno.dlopen(soname, voskSymbols);
    } catch (e) {
      console.error(
        `Error loading Vosk library. Tried local: '${sonameLocal}' and system: '${soname}'.`,
      );
      throw e;
    }
  }
} else {
  try {
    // 2. try to load library installed in the system
    libvosk = Deno.dlopen(soname, voskSymbols);
  } catch (e) {
    console.error(
      `Error loading Vosk library. Tried local: '${sonameLocal}' and system: '${soname}'.`,
    );
    throw e;
  }
}

// --- Helper Functions ---

/** Encodes a JavaScript string to a null-terminated C string (Uint8Array). */
function encodeCString(value: string): Uint8Array {
  return new TextEncoder().encode(value + "\0");
}

/** Reads a C string (char*) from a Deno pointer. Returns null if pointer is null. */
function readCString(pointer: Deno.PointerValue): string | null {
  if (pointer === null) {
    return null;
  }
  try {
    return Deno.UnsafePointerView.getCString(pointer);
  } catch (e) {
    console.error("Failed to read C string from pointer");
    throw e;
  }
}

// --- Exported Vosk API ---

/**
 * Set log level for Kaldi messages
 * @param level The higher, the more verbose. 0 for infos and errors. Less than 0 for silence.
 */
export function setLogLevel(level: number): void {
  libvosk.symbols.vosk_set_log_level(level);
}

/**
 * Build a Model from a model file path.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
export class Model {
  /** @internal */
  public handle: Deno.PointerValue | null = null; // Store the native pointer

  /**
   * Build a Model to be used with the voice recognition. Each language should have it's own Model
   * for the speech recognition to work.
   * @param modelPath The absolute or relative pathname to the model directory
   * @see models [models](https://alphacephei.com/vosk/models)
   */
  constructor(modelPath: string) {
    const encodedPath = encodeCString(modelPath);
    this.handle = libvosk.symbols.vosk_model_new(encodedPath);
    if (this.handle === null) {
      // PointerValue 0 is equivalent to NULL pointer
      throw new Error(`Failed to create Vosk model from path: ${modelPath}`);
    }
  }

  /**
   * Releases the model memory.
   *
   * The model object is reference-counted so if some recognizer
   * depends on this model, model might still stay alive. When
   * last recognizer is released, model will be released too.
   */
  free(): void {
    if (this.handle) {
      libvosk.symbols.vosk_model_free(this.handle);
      this.handle = null; // Prevent double-free
    }
  }
}

/**
 * Build a Speaker Model from a speaker model file path.
 * The Speaker Model enables speaker identification.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
export class SpeakerModel {
  /** @internal */
  public handle: Deno.PointerValue | null = null; // Store the native pointer

  /**
   * Loads speaker model data from the file and returns the model object
   * @param modelPath the path of the model on the filesystem
   * @see models [models](https://alphacephei.com/vosk/models)
   */
  constructor(modelPath: string) {
    const encodedPath = encodeCString(modelPath);
    this.handle = libvosk.symbols.vosk_spk_model_new(encodedPath);
    if (this.handle === null) {
      throw new Error(
        `Failed to create Vosk speaker model from path: ${modelPath}`,
      );
    }
  }

  /**
   * Releases the speaker model memory.
   *
   * The model object is reference-counted so if some recognizer
   * depends on this model, model might still stay alive. When
   * last recognizer is released, model will be released too.
   */
  free(): void {
    if (this.handle) {
      libvosk.symbols.vosk_spk_model_free(this.handle);
      this.handle = null; // Prevent double-free
    }
  }
}

// Utility types for XOR logic (same as original)
type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };
type XOR<T, U> = (T | U) extends object
  ? (Without<T, U> & U) | (Without<U, T> & T)
  : T | U;

/**
 * Create a Recognizer that will be able to transform audio streams into text using a Model.
 * @template T Extra parameter for speaker or grammar options.
 * @see Model
 */
export class Recognizer<
  T extends XOR<SpeakerRecognizerParam, Partial<GrammarRecognizerParam>>,
> {
  /** @internal */
  public handle: Deno.PointerValue | null = null; // Store the native pointer

  /**
   * Create a Recognizer that will handle speech to text recognition.
   * @constructor
   * @param param The Recognizer parameters, including model, sampleRate, and optional grammar or speakerModel.
   *
   *  Sometimes when you want to improve recognition accuracy and when you don't need
   *  to recognize large vocabulary you can specify a list of phrases to recognize. This
   *  will improve recognizer speed and accuracy but might return [unk] if user said
   *  something different.
   *
   *  Only recognizers with lookahead models support this type of quick configuration.
   *  Precompiled HCLG graph models are not supported.
   */
  constructor(param: T & BaseRecognizerParam) {
    const { model, sampleRate } = param;

    // Prevent using both grammar and speakerModel simultaneously
    if (
      Object.hasOwn(param, "speakerModel") &&
      Object.hasOwn(param, "grammar")
    ) {
      throw new Error(
        "grammar and speakerModel cannot be used together in the constructor.",
      );
    }

    if (Object.hasOwn(param, "speakerModel") && param.speakerModel) {
      // Speaker recognizer
      const spkModel = param.speakerModel;
      this.handle = libvosk.symbols.vosk_recognizer_new_spk(
        model.handle,
        sampleRate,
        spkModel.handle,
      );
    } else if (Object.hasOwn(param, "grammar") && param.grammar) {
      // Grammar recognizer
      const grammarJson = JSON.stringify(param.grammar);
      const encodedGrammar = encodeCString(grammarJson);
      this.handle = libvosk.symbols.vosk_recognizer_new_grm(
        model.handle,
        sampleRate,
        encodedGrammar,
      );
    } else {
      // Base recognizer
      this.handle = libvosk.symbols.vosk_recognizer_new(
        model.handle,
        sampleRate,
      );
    }

    if (this.handle === null) {
      throw new Error("Failed to create Vosk recognizer.");
    }
  }

  /**
   * Releases the recognizer memory.
   */
  free(): void {
    if (this.handle) {
      libvosk.symbols.vosk_recognizer_free(this.handle);
      this.handle = null; // Prevent double-free
    }
  }

  /** Configures recognizer to output n-best results. */
  setMaxAlternatives(maxAlternatives: number): void {
    libvosk.symbols.vosk_recognizer_set_max_alternatives(
      this.handle,
      maxAlternatives,
    );
  }

  /** Configures recognizer to output words with times. */
  setWords(words: boolean): void {
    libvosk.symbols.vosk_recognizer_set_words(this.handle, words);
  }

  /** Configures recognizer to output partial words with times. */
  setPartialWords(partialWords: boolean): void {
    libvosk.symbols.vosk_recognizer_set_partial_words(
      this.handle,
      partialWords,
    );
  }

  /** Adds speaker recognition model to an already created recognizer. */
  setSpkModel(spkModel: SpeakerModel): void {
    libvosk.symbols.vosk_recognizer_set_spk_model(
      this.handle,
      spkModel.handle,
    );
  }

  /**
   * Synchronously accept and process a new chunk of voice data.
   *
   * @param data Audio data in PCM 16-bit mono format (as Uint8Array).
   * @returns `true` if silence is detected (or end of segment in grammar mode), indicating a result might be ready.
   */
  acceptWaveform(data: Uint8Array): boolean {
    return libvosk.symbols.vosk_recognizer_accept_waveform(
      this.handle,
      data,
      data.byteLength, // Use byteLength for buffer size
    );
  }

  // TODO: async

  /**
   * Returns the speech recognition result as a raw JSON string.
   * Call this after `acceptWaveform` returns `true` or after feeding all data.
   * @returns JSON string result, or null if reading fails.
   */
  resultString(): string | null {
    const resultPtr = libvosk.symbols.vosk_recognizer_result(this.handle);
    return readCString(resultPtr);
  }

  /**
   * Returns the parsed speech recognition result.
   * @returns The parsed result object, cast to the appropriate type based on Recognizer options.
   */
  result(): RecognizerResult<T> | null {
    const jsonString = this.resultString();
    if (jsonString) {
      return JSON.parse(jsonString) as RecognizerResult<T>;
    } else {
      return null;
    }
  }

  /**
   * Returns the partial speech recognition result as a raw JSON string.
   * Result may change as more data is processed.
   * @returns JSON string partial result, or null if reading fails.
   */
  partialResultString(): string | null {
    const resultPtr = libvosk.symbols.vosk_recognizer_partial_result(
      this.handle,
    );
    return readCString(resultPtr);
  }

  /**
   * Returns the parsed partial speech recognition result.
   * @returns The parsed partial result object.
   */
  partialResult(): PartialResults | null {
    const jsonString = this.partialResultString();
    if (jsonString) {
      return JSON.parse(jsonString) as PartialResults;
    } else {
      return null;
    }
  }

  /**
   * Returns the final speech recognition result as a raw JSON string.
   * Use this at the very end of processing to flush internal buffers.
   * @returns JSON string final result, or null if reading fails.
   */
  finalResultString(): string | null {
    const resultPtr = libvosk.symbols.vosk_recognizer_final_result(
      this.handle,
    );
    return readCString(resultPtr);
  }

  /**
   * Returns the parsed final speech recognition result.
   * Use this at the very end of processing.
   * @returns The parsed final result object.
   */
  finalResult(): RecognizerResult<T> | null {
    const jsonString = this.finalResultString();
    if (jsonString) {
      return JSON.parse(jsonString) as RecognizerResult<T>;
    } else {
      return null;
    }
  }

  /**
   * Resets the recognizer, clearing partial results.
   * Recognition can then continue from scratch.
   */
  reset(): void {
    libvosk.symbols.vosk_recognizer_reset(this.handle);
  }
}
