# vosk-api-kotlin

The vosk-api wrapped using Kotlin Multiplatform.

## Usage

The following are ways to use this wrapper.

### JVM

For Java & Android targets.

```kotlin
dependencoes {
    val voskVersion = "0.4.0-alpha0"

    // Generic
    implementation("com.alphacephei:vosk-api-kotlin:$voskVersion")

    // Android
    implementation("com.alphacephei:vosk-api-kotlin-android:$voskVersion")
}
```

## Building

To build this project, follow the following steps.

1. Install `libvosk`.
This can be done from [source][source install] (parent monorepo) 
or [downloaded][download].
2. Download a [Vosk model](https://alphacephei.com/vosk/models) to use.
  - It is suggested to use a small model to speed up tests.
3. Once both are downloaded and placed into a proper location (hopefully following UNIX specification).
Set the following environment variables:
  - `VOSK_MODEL` to the path of the model.
  - `VOSK_PATH` to the path of `libvosk`.
These are used by the various tests to operate.
4. Now that the required steps are complete, one can run `./gradlew build`.

## Kotlin/Native

Currently, the native target is disabled due to a lack of vosk-api packaging on platforms.
Further worsened by the fact that installing the vosk-api on Linux systems is a chore.

First, either install from [source][source install]
or [download][download] and install into the proper unix directories as expected in
[libvosk.def](./src/nativeInterop/cinterop/libvosk.def).

To enable development for Kotlin/Native, do either for the following.
- Add `NATIVE_EXPERIMENT=true` to your environment.
- Go into [build.gradle.kts](./build.gradle.kts) & find `enableNative` & set the right side to true.

Afterwards, when syncing the project, the native source sets will become available to work on.
It is suggested to run `cinteropLibvoskNative` to generate the Kotlin C bindings to work with.

## Future

- Possibly target Kotlin/JS
- Possibly target Kotlin/Objective-C (?)

[source install]: https://alphacephei.com/vosk/install
[download]: https://github.com/alphacep/vosk-api/releases/latest