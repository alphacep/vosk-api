package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"encoding/json"

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

	// we can check if word is in the vocabulary
	// fmt.Println(model.FindWord("air"))

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
			fmt.Println(rec.Result())
		}
	}

	// Unmarshal example for final result
	var jres map[string]interface{}
	json.Unmarshal([]byte(rec.FinalResult()), &jres)
	fmt.Println(jres["text"])
}
