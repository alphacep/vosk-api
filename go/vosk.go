package vosk

// #cgo CPPFLAGS: -I ${SRCDIR}/../src
// #cgo LDFLAGS: -L ${SRCDIR}/../src -lvosk -ldl -lpthread
// #include <stdlib.h>
// #include <vosk_api.h>
import "C"

// VoskModel contains a reference to the C VoskModel
type VoskModel struct {
    model *C.struct_VoskModel
}

// VoskSpkModel contains a reference to the C VoskSpkModel
type VoskSpkModel struct {
    spkModel *C.struct_VoskSpkModel
}

// VoskRecognizer contains a reference to the C VoskRecognizer
type VoskRecognizer struct {
    rec *C.struct_VoskRecognizer
}

func VoskFinalResult(recognizer *VoskRecognizer, buffer []byte) string {
    cbuf := C.CBytes(buffer)
    defer C.free(cbuf)
    _ = C.vosk_recognizer_accept_waveform(recognizer.rec, (*C.char)(cbuf), C.int(len(buffer)))
    result := C.GoString(C.vosk_recognizer_final_result(recognizer.rec))
    return result
}

// NewModel creates a new VoskModel instance
func NewModel(modelPath string) (*VoskModel, error) {
    var internal *C.struct_VoskModel
    internal = C.vosk_model_new(C.CString(modelPath))
    model := &VoskModel{model: internal}
    return model, nil
}

// NewRecognizer creates a new VoskRecognizer instance
func NewRecognizer(model *VoskModel) (*VoskRecognizer, error) {
    var internal *C.struct_VoskRecognizer
    internal = C.vosk_recognizer_new(model.model, 16000.0)
    rec := &VoskRecognizer{rec: internal}
    return rec, nil
}

func freeModel(model *VoskModel) {
    C.vosk_model_free(model.model)
}

func freeRecognizer(recognizer *VoskRecognizer) {
    C.vosk_recognizer_free(recognizer.rec)
}

// NewSpkModel creates a new VoskSpkModel instance
func NewSpkModel(spkModelPath string) (*VoskSpkModel, error) {
    var internal *C.struct_VoskSpkModel
    internal = C.vosk_spk_model_new(C.CString(spkModelPath))
    spkModel := &VoskSpkModel{spkModel: internal}
    return spkModel, nil
}
