# Deno Vosk API Wrapper

This is an FFI wrapper for the Vosk library for Deno.

## Usage

These bindings largely follow the native Vosk C API, adapted for Deno's FFI
interface. Some advanced methods might not be fully implemented yet.

See the
[demo folder](https://github.com/alphacep/vosk-api/tree/master/denojs/demo) for
example usage.

**Important:** Unlike the Node.js bindings (`vosk`), this Deno wrapper **does
not bundle the native Vosk libraries**. You need to ensure the correct `libvosk`
shared library (`.so`, `.dylib`, or `.dll`) is available on your system.

The wrapper attempts to load the native library using the following search
order:

1. **Environment Variable:** Checks if the `VOSK_LIB_DIR_PATH` environment
   variable is set. If it is, the wrapper attempts to load the library directly
   from the specified directory (e.g., `$VOSK_LIB_DIR_PATH/libvosk.so`). This is
   the recommended way to specify a custom library location.
2. **Relative to the module (if possible):** If `VOSK_LIB_DIR_PATH` is not set
   and the script's location (`import.meta.dirname`) can be determined, it looks
   inside a `lib/<os-arch>` subdirectory relative to where this Deno module
   (`mod.ts`) is located (e.g., `lib/linux-x86_64/libvosk.so`). This method
   maybe removed in the future, since deno doenst really have a concept of a
   package.
3. **System library paths:** If the above methods fail or are not applicable, it
   tries loading the library by its standard name (`libvosk.so`,
   `libvosk.dylib`, `libvosk.dll`), relying on the OS's standard dynamic library
   loading mechanism (e.g., `LD_LIBRARY_PATH` on Linux, `PATH` on Windows,
   system paths on macOS).

**example**

```ts
import * as vosk from "https://raw.githubusercontent.com/alphacep/vosk-api/v0.3.50/denojs/mod.ts";
import wav from "npm:wav";
import fs from "node:fs";
import process from "node:process";
import { Readable } from "node:stream";

const MODEL_PATH = "model";
const FILE_NAME = "test.wav";

if (!fs.existsSync(MODEL_PATH)) {
  console.log(
    "Please download the model from https://alphacephei.com/vosk/models and unpack as " +
      MODEL_PATH + " in the current folder.",
  );
  process.exit();
}

if (process.argv.length > 2) {
  FILE_NAME = process.argv[2];
}

vosk.setLogLevel(0);
const model = new vosk.Model(MODEL_PATH);

const wfReader = new wav.Reader();
const wfReadable = new Readable().wrap(wfReader);

wfReader.on("format", async ({ audioFormat, sampleRate, channels }) => {
  if (audioFormat != 1 || channels != 1) {
    console.error("Audio file must be WAV format mono PCM.");
    process.exit(1);
  }
  const rec = new vosk.Recognizer({ model: model, sampleRate: sampleRate });
  rec.setMaxAlternatives(10);
  rec.setWords(true);
  rec.setPartialWords(true);
  for await (const data of wfReadable) {
    const end_of_speech = rec.acceptWaveform(data);
    if (end_of_speech) {
      console.log(JSON.stringify(rec.result(), null, 4));
    } else {
      console.log(JSON.stringify(rec.partialResult(), null, 4));
    }
  }
  console.log(JSON.stringify(rec.finalResult(rec), null, 4));
  rec.free();
});

fs.createReadStream(FILE_NAME, { "highWaterMark": 4096 }).pipe(wfReader).on(
  "finish",
  function () {
    model.free();
  },
);
```

## About Vosk

Vosk is an offline open source speech recognition toolkit. It enables speech
recognition for 20+ languages and dialects - English, Indian English, German,
French, Spanish, Portuguese, Chinese, Russian, Turkish, Vietnamese, Italian,
Dutch, Catalan, Arabic, Greek, Farsi, Filipino, Ukrainian, Kazakh, Swedish,
Japanese, Esperanto, Hindi, Czech, Polish. More to come.

Vosk models are small (50 Mb) but provide continuous large vocabulary
transcription, zero-latency response with streaming API, reconfigurable
vocabulary and speaker identification.

Vosk supplies speech recognition for chatbots, smart home appliances, virtual
assistants. It can also create subtitles for movies, transcription for lectures
and interviews.

Vosk scales from small devices like Raspberry Pi or Android smartphone to big
clusters.

# Documentation

For installation instructions (for the underlying Vosk library and models),
examples, and documentation visit the
[Vosk Website](https://alphacephei.com/vosk). See also the main project on
[Github](https://github.com/alphacep/vosk-api).
