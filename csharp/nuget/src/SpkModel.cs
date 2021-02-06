namespace Vosk {

public class SpkModel : global::System.IDisposable {
  private global::System.Runtime.InteropServices.HandleRef handle;

  internal SpkModel(global::System.IntPtr cPtr) {
    handle = new global::System.Runtime.InteropServices.HandleRef(this, cPtr);
  }

  internal static global::System.Runtime.InteropServices.HandleRef getCPtr(SpkModel obj) {
    return (obj == null) ? new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero) : obj.handle;
  }

  ~SpkModel() {
    Dispose(false);
  }

  public void Dispose() {
    Dispose(true);
    global::System.GC.SuppressFinalize(this);
  }

  protected virtual void Dispose(bool disposing) {
    lock(this) {
      if (handle.Handle != global::System.IntPtr.Zero) {
        VoskPINVOKE.delete_SpkModel(handle);
        handle = new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero);
      }
    }
  }

  public SpkModel(string model_path) : this(VoskPINVOKE.new_SpkModel(model_path)) {
  }

}

}
