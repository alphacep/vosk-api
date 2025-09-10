package vosk

// #cgo CPPFLAGS: -I ${SRCDIR}/../src
// #cgo !windows LDFLAGS: -L ${SRCDIR}/../src -lvosk -ldl -lpthread
// #cgo windows LDFLAGS: -L ${SRCDIR}/../src -lvosk -lpthread
// #include <stdlib.h>
// #include <vosk_api.h>
import "C"
import "unsafe"

// VoskBatchModel contains a reference to the C VoskBatchModel
type VoskBatchModel struct {
	model *C.struct_VoskBatchModel
}

// NewBatchModel creates a new VoskBatchModel instance
func NewBatchModel(modelPath string) (*VoskBatchModel, error) {
	cmodelPath := C.CString(modelPath)
	defer C.free(unsafe.Pointer(cmodelPath))
	internal := C.vosk_batch_model_new(cmodelPath)
	model := &VoskBatchModel{model: internal}
	return model, nil
}

func (m *VoskBatchModel) Free() {
	C.vosk_batch_model_free(m.model)
}

func (m *VoskBatchModel) Wait() {
	C.vosk_batch_model_wait(m.model);
}

func freeBatchModel(model *VoskBatchModel) {
	C.vosk_batch_model_free(model.model)
}

// VoskBatchRecognizer contains a reference to the C VoskBatchRecognizer
type VoskBatchRecognizer struct {
	rec *C.struct_VoskBatchRecognizer
}

func freeBatchRecognizer(recognizer *VoskBatchRecognizer) {
	C.vosk_batch_recognizer_free(recognizer.rec)
}

func (r *VoskBatchRecognizer) Free() {
	C.vosk_batch_recognizer_free(r.rec)
}

// NewBatchRecognizer creates a new VoskBatchRecognizer instance
func NewBatchRecognizer(model *VoskBatchModel, sampleRate float64) (*VoskBatchRecognizer, error) {
	internal := C.vosk_batch_recognizer_new(model.model, C.float(sampleRate))
	rec := &VoskBatchRecognizer{rec: internal}
	return rec, nil
}

// AcceptWaveform accepts and processes a new chunk of the voice data.
func (r *VoskBatchRecognizer) AcceptWaveform(buffer []byte) {
	cbuf := C.CBytes(buffer)
	defer C.free(cbuf)
	C.vosk_batch_recognizer_accept_waveform(r.rec, (*C.char)(cbuf), C.int(len(buffer)))
}

/** Set NLSML output
 * @param nlsml - boolean value
 */
//void vosk_batch_recognizer_set_nlsml(VoskBatchRecognizer *recognizer, int nlsml);

func (r *VoskBatchRecognizer) SetNlsml(nlsml int) {
	C.vosk_batch_recognizer_set_nlsml(r.rec, C.int(nlsml))
}

/** Closes the stream */
//void vosk_batch_recognizer_finish_stream(VoskBatchRecognizer *recognizer);

func (r *VoskBatchRecognizer) FinishStream() {
	C.vosk_batch_recognizer_finish_stream(r.rec)
}

/** Return results */
//const char *vosk_batch_recognizer_front_result(VoskBatchRecognizer *recognizer);

func (r *VoskBatchRecognizer) FrontResult() string {
	return C.GoString(C.vosk_batch_recognizer_front_result(r.rec))
}

/** Release and free first retrieved result */
//void vosk_batch_recognizer_pop(VoskBatchRecognizer *recognizer);

func (r *VoskBatchRecognizer) Pop() {
	C.vosk_batch_recognizer_pop(r.rec)
}

/** Get amount of pending chunks for more intelligent waiting */
//int vosk_batch_recognizer_get_pending_chunks(VoskBatchRecognizer *recognizer);
func (r *VoskBatchRecognizer) GetPendingChunks() int {
	i := C.vosk_batch_recognizer_get_pending_chunks(r.rec)
	return int(i)
}
