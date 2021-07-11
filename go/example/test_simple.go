package main

import (
    "flag"
    "os"
    "github.com/alphacep/vosk-api/go"
)

func main() {
    var filename string
    flag.StringVar(&filename, "f", "", "file to transcribe")
    flag.Parse()
    model, err := vosk.NewModel("model")
    rec, err := vosk.NewRecognizer(model)

    file, err := os.Open(filename)
    if err != nil {
        panic(err)
    }
    defer file.Close()

    fileinfo, err := file.Stat()
    if err != nil {
        panic(err)
    }

    filesize := fileinfo.Size()
    buffer := make([]byte, filesize)

    _, err = file.Read(buffer)
    if err != nil {
        panic(err)
    }

    println(vosk.VoskFinalResult(rec, buffer))
}
