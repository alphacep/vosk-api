namespace Vosk {

public class VoskRecognizer : System.IDisposable {
  private System.Runtime.InteropServices.HandleRef handle;

  internal VoskRecognizer(System.IntPtr cPtr) {
    handle = new System.Runtime.InteropServices.HandleRef(this, cPtr);
  }

  internal static System.Runtime.InteropServices.HandleRef getCPtr(VoskRecognizer obj) {
    return (obj == null) ? new System.Runtime.InteropServices.HandleRef(null, System.IntPtr.Zero) : obj.handle;
  }

  ~VoskRecognizer() {
    Dispose(false);
  }

  public void Dispose() {
    Dispose(true);
    System.GC.SuppressFinalize(this);
  }

  protected virtual void Dispose(bool disposing) {
    lock(this) {
      if (handle.Handle != System.IntPtr.Zero) {
        VoskPINVOKE.delete_VoskRecognizer(handle);
        handle = new System.Runtime.InteropServices.HandleRef(null, System.IntPtr.Zero);
      }
    }
  }

  public VoskRecognizer(Model model, float sample_rate) : this(VoskPINVOKE.new_VoskRecognizer(Model.getCPtr(model), sample_rate)) {
  }

  public VoskRecognizer(Model model, float sample_rate, SpkModel spk_model) : this(VoskPINVOKE.new_VoskRecognizerSpk(Model.getCPtr(model), sample_rate, SpkModel.getCPtr(spk_model))) {
  }

  public VoskRecognizer(Model model, float sample_rate, string grammar) : this(VoskPINVOKE.new_VoskRecognizerGrm(Model.getCPtr(model), sample_rate, grammar)) {
  }

  public void SetMaxAlternatives(int max_alternatives) {
    VoskPINVOKE.VoskRecognizer_SetMaxAlternatives(handle, max_alternatives);
  }

  public void SetWords(bool words) {
    VoskPINVOKE.VoskRecognizer_SetWords(handle, words ? 1 : 0);
  }

  public void SetPartialWords(bool partial_words) {
    VoskPINVOKE.VoskRecognizer_SetPartialWords(handle, partial_words ? 1 : 0);
  }

  public void SetSpkModel(SpkModel spk_model) {
    VoskPINVOKE.VoskRecognizer_SetSpkModel(handle, SpkModel.getCPtr(spk_model));
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

  private static string PtrToStringUTF8(System.IntPtr ptr) {
    int len = 0;
    while (System.Runtime.InteropServices.Marshal.ReadByte(ptr, len) != 0)
        len++;
    byte[] array = new byte[len];
    System.Runtime.InteropServices.Marshal.Copy(ptr, array, 0, len);
    return System.Text.Encoding.UTF8.GetString(array);
  }

  public string Result() {
    return PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_Result(handle));
  }

  public string PartialResult() {
    return PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_PartialResult(handle));
  }

  public string FinalResult() {
    return PtrToStringUTF8(VoskPINVOKE.VoskRecognizer_FinalResult(handle));
  }

  public void Reset() {
    VoskPINVOKE.VoskRecognizer_Reset(handle);
  }

}

}
