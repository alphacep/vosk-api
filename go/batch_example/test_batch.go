package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"os"

	vosk "github.com/alphacep/vosk-api/go"
)

func main() {
	var filename string
	flag.StringVar(&filename, "f", "", "file to transcribe")
	flag.Parse()

	vosk.GPUInit()

	model, err := vosk.NewBatchModel("model")
	if err != nil {
		log.Fatal(err)
	}

	rec, err := vosk.NewBatchRecognizer(model, 16000.0)
	if err != nil {
		log.Fatal(err)
	}

	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	buf := make([]byte, 8000)

	for {
		if _, err := file.Read(buf); err != nil {
			if err != io.EOF {
				log.Fatal(err)
			}

			break
		}
		rec.AcceptWaveform(buf)
		model.Wait()
		if rec.FrontResult() != "" {
			fmt.Println(rec.FrontResult())
			rec.Pop()
		}
	}
	// Is this needed? rec.FinishStream()
}
