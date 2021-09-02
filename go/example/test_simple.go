package main

import (
	"bufio"
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

	model, err := vosk.NewModel("model")
	if err != nil {
		log.Fatal(err)
	}

	sampleRate := 16000.0
	rec, err := vosk.NewRecognizer(model, sampleRate)
	if err != nil {
		log.Fatal(err)
	}
	rec.SetWords(1)

	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	reader := bufio.NewReader(file)
	buf := make([]byte, 4096)

	for {
		_, err := reader.Read(buf)
		if err != nil {
			if err != io.EOF {
				log.Fatal(err)
			}

			break
		}

		if rec.AcceptWaveform(buf) != 0 {
			fmt.Println(string(rec.Result()))
		}
	}

	fmt.Println(string(rec.FinalResult()))
}
