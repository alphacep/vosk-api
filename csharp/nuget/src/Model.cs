namespace Vosk {

public class Model : global::System.IDisposable {
  private global::System.Runtime.InteropServices.HandleRef handle;

  internal Model(global::System.IntPtr cPtr) {
    handle = new global::System.Runtime.InteropServices.HandleRef(this, cPtr);
  }

  internal static global::System.Runtime.InteropServices.HandleRef getCPtr(Model obj) {
    return (obj == null) ? new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero) : obj.handle;
  }

  ~Model() {
    Dispose(false);
  }

  public void Dispose() {
    Dispose(true);
    global::System.GC.SuppressFinalize(this);
  }

  protected virtual void Dispose(bool disposing) {
    lock(this) {
      if (handle.Handle != global::System.IntPtr.Zero) {
        VoskPINVOKE.delete_Model(handle);
        handle = new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero);
      }
    }
  }

  public Model(string model_path) : this(VoskPINVOKE.new_Model(model_path)) {
  }

  public int FindWord(string word) {
    return VoskPINVOKE.Model_vosk_model_find_word(handle, word);
  }

}

}
