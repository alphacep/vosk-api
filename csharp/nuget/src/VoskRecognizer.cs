namespace Vosk {

public class VoskRecognizer : global::System.IDisposable {
  private global::System.Runtime.InteropServices.HandleRef handle;

  internal VoskRecognizer(global::System.IntPtr cPtr) {
    handle = new global::System.Runtime.InteropServices.HandleRef(this, cPtr);
  }

  internal static global::System.Runtime.InteropServices.HandleRef getCPtr(VoskRecognizer obj) {
    return (obj == null) ? new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero) : obj.handle;
  }

  ~VoskRecognizer() {
    Dispose(false);
  }

  public void Dispose() {
    Dispose(true);
    global::System.GC.SuppressFinalize(this);
  }

  protected virtual void Dispose(bool disposing) {
    lock(this) {
      if (handle.Handle != global::System.IntPtr.Zero) {
        VoskPINVOKE.delete_VoskRecognizer(handle);
        handle = new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero);
      }
    }
  }

  public VoskRecognizer(Model model, float sample_rate) : this(VoskPINVOKE.new_VoskRecognizer(Model.getCPtr(model), sample_rate)) {
  }

  public VoskRecognizer(Model model, SpkModel spk_model, float sample_rate) : this(VoskPINVOKE.new_VoskRecognizerSpk(Model.getCPtr(model), SpkModel.getCPtr(spk_model), sample_rate)) {
  }

  public VoskRecognizer(Model model, float sample_rate, string grammar) : this(VoskPINVOKE.new_VoskRecognizerGrm(Model.getCPtr(model), sample_rate, grammar)) {
  }

  public bool AcceptWaveform(byte[] data, int len) {
    return VoskPINVOKE.VoskRecognizer_AcceptWaveform(handle, data, len);
  }

  public bool AcceptWaveform(short[] sdata, int len) {
    return VoskPINVOKE.VoskRecognizer_AcceptWaveformShort(handle, sdata, len);
  }

  public bool AcceptWaveform(float[] fdata, int len) {
    return VoskPINVOKE.VoskRecognizer_AcceptWaveformFloat(handle, fdata, len);
  }

  public string Result() {
    return global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_Result(handle));
  }

  public string PartialResult() {
    return global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_PartialResult(handle));
  }

  public string FinalResult() {
    return global::System.Runtime.InteropServices.Marshal.PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_FinalResult(handle));
  }

}

}
