package vosk

// #cgo CPPFLAGS: -I ${SRCDIR}/../src
// #cgo !windows LDFLAGS: -L ${SRCDIR}/../src -lvosk -ldl -lpthread
// #cgo windows LDFLAGS: -L ${SRCDIR}/../src -lvosk -lpthread
// #include <stdlib.h>
// #include <vosk_api.h>
import "C"
import "unsafe"

// VoskModel contains a reference to the C VoskModel
type VoskModel struct {
	model *C.struct_VoskModel
}

// NewModel creates a new VoskModel instance
func NewModel(modelPath string) *VoskModel {
	cmodelPath := C.CString(modelPath)
	defer C.free(unsafe.Pointer(cmodelPath))
	internal := C.vosk_model_new(cmodelPath)
	model := &VoskModel{model: internal}
	return model
}

func (m *VoskModel) Free() {
	C.vosk_model_free(m.model)
}

func freeModel(model *VoskModel) {
	C.vosk_model_free(model.model)
}

// FindWord checks if a word can be recognized by the model.
// Returns the word symbol if the word exists inside the model or
// -1 otherwise.
func (m *VoskModel) FindWord(word string) int {
	cstr := C.CString(word)
	defer C.free(unsafe.Pointer(cstr))
	i := C.vosk_model_find_word(m.model, cstr)
	return int(i)
}

// VoskSpkModel contains a reference to the C VoskSpkModel
type VoskSpkModel struct {
	spkModel *C.struct_VoskSpkModel
}

// NewSpkModel creates a new VoskSpkModel instance
func NewSpkModel(spkModelPath string) (*VoskSpkModel, error) {
	cspkModelPath := C.CString(spkModelPath)
	defer C.free(unsafe.Pointer(cspkModelPath))
	internal := C.vosk_spk_model_new(cspkModelPath)
	spkModel := &VoskSpkModel{spkModel: internal}
	return spkModel, nil
}

func freeSpkModel(model *VoskSpkModel) {
	C.vosk_spk_model_free(model.spkModel)
}

func (s *VoskSpkModel) Free() {
	C.vosk_spk_model_free(s.spkModel)
}

// VoskRecognizer contains a reference to the C VoskRecognizer
type VoskRecognizer struct {
	rec *C.struct_VoskRecognizer
}

func freeRecognizer(recognizer *VoskRecognizer) {
	C.vosk_recognizer_free(recognizer.rec)
}

func (r *VoskRecognizer) Free() {
	C.vosk_recognizer_free(r.rec)
}

// NewRecognizer creates a new VoskRecognizer instance
func NewRecognizer(model *VoskModel, sampleRate float64) (*VoskRecognizer, error) {
	internal := C.vosk_recognizer_new(model.model, C.float(sampleRate))
	rec := &VoskRecognizer{rec: internal}
	return rec, nil
}

// NewRecognizerSpk creates a new VoskRecognizer instance with a speaker model.
func NewRecognizerSpk(model *VoskModel, sampleRate float64, spkModel *VoskSpkModel) (*VoskRecognizer, error) {
	internal := C.vosk_recognizer_new_spk(model.model, C.float(sampleRate), spkModel.spkModel)
	rec := &VoskRecognizer{rec: internal}
	return rec, nil
}

// NewRecognizerGrm creates a new VoskRecognizer instance with the phrase list.
func NewRecognizerGrm(model *VoskModel, sampleRate float64, grammar string) (*VoskRecognizer, error) {
	cgrammar := C.CString(grammar)
	defer C.free(unsafe.Pointer(cgrammar))
	internal := C.vosk_recognizer_new_grm(model.model, C.float(sampleRate), cgrammar)
	rec := &VoskRecognizer{rec: internal}
	return rec, nil
}

// SetSpkModel adds a speaker model to an already initialized recognizer.
func (r *VoskRecognizer) SetSpkModel(spkModel *VoskSpkModel) {
	C.vosk_recognizer_set_spk_model(r.rec, spkModel.spkModel)
}

// SetGrm sets which phrases to recognize on an already initialized recognizer.
func (r *VoskRecognizer) SetGrm(grammar string) {
	cgrammar := C.CString(grammar)
	defer C.free(unsafe.Pointer(cgrammar))
	C.vosk_recognizer_set_grm(r.rec, cgrammar)
}

// SetMaxAlternatives configures the recognizer to output n-best results.
func (r *VoskRecognizer) SetMaxAlternatives(maxAlternatives int) {
	C.vosk_recognizer_set_max_alternatives(r.rec, C.int(maxAlternatives))
}

// SetWords enables words with times in the ouput.
func (r *VoskRecognizer) SetWords(words int) {
	C.vosk_recognizer_set_words(r.rec, C.int(words))
}

// SetPartialWords enables words with times in the partial ouput.
func (r *VoskRecognizer) SetPartialWords(words int) {
	C.vosk_recognizer_set_partial_words(r.rec, C.int(words))
}

// SetEndpointerDelays sets the recognition timeouts, where startMax
// is the timeout for stopping recognition in case of initial silence
// (usually around 5), end is the timeout for stopping recognition
// in milliseconds after we recognized something (usually around 0.5-1.0),
// and max is the timeout for forcing utterance end in milliseconds
// (usually around 20-30).
func (r *VoskRecognizer) SetEndpointerDelays(startMax, end, max float64) {
	C.vosk_recognizer_set_endpointer_delays(r.rec, C.float(startMax), C.float(end), C.float(max))
}

// AcceptWaveform accepts and processes a new chunk of the voice data.
func (r *VoskRecognizer) AcceptWaveform(buffer []byte) int {
	cbuf := C.CBytes(buffer)
	defer C.free(cbuf)
	i := C.vosk_recognizer_accept_waveform(r.rec, (*C.char)(cbuf), C.int(len(buffer)))
	return int(i)
}

// Result returns a speech recognition result.
func (r *VoskRecognizer) Result() string {
	return C.GoString(C.vosk_recognizer_result(r.rec))
}

// PartialResult returns a partial speech recognition result.
func (r *VoskRecognizer) PartialResult() string {
	return C.GoString(C.vosk_recognizer_partial_result(r.rec))
}

// FinalResult returns a speech recognition result. Same as result, but doesn't wait
// for silence.
func (r *VoskRecognizer) FinalResult() string {
	return C.GoString(C.vosk_recognizer_final_result(r.rec))
}

// Reset resets the recognizer.
func (r *VoskRecognizer) Reset() {
	C.vosk_recognizer_reset(r.rec)
}

type LogLevel int

const Disabled LogLevel = -1
const Default LogLevel = 0
const Verbose LogLevel = 1

// SetLogLevel sets the log level for Kaldi messages.
func SetLogLevel(logLevel LogLevel) {
	C.vosk_set_log_level(C.int(logLevel))
}

// GPUInit automatically selects a CUDA device and allows multithreading.
func GPUInit() {
	C.vosk_gpu_init()
}

// GPUThreadInit inits CUDA device in a multi-threaded environment.
func GPUThreadInit() {
	C.vosk_gpu_thread_init()
}
