using System;

namespace Vosk
{
    public class BatchModel : global::System.IDisposable
    {
        private global::System.Runtime.InteropServices.HandleRef handle;

        internal BatchModel(global::System.IntPtr cPtr)
        {
            handle = new global::System.Runtime.InteropServices.HandleRef(this, cPtr);
        }

        internal static global::System.Runtime.InteropServices.HandleRef getCPtr(BatchModel obj)
        {
            return (obj == null) ? new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero) : obj.handle;
        }

        ~BatchModel()
        {
            Dispose(false);
        }

        public void Dispose()
        {
            Dispose(true);
            global::System.GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            lock (this)
            {
                if (handle.Handle != global::System.IntPtr.Zero)
                {
                    VoskPINVOKE.delete_BatchModel(handle);
                    handle = new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero);
                }
            }
        }

        public BatchModel(string model_path) : this(VoskPINVOKE.new_BatchModel(model_path))
        {
        }

        public void WaitForCompletion()
        {
            if (handle.Handle != global::System.IntPtr.Zero)
            {
                VoskPINVOKE.wait_BatchModel(handle);
            }
        }
    }

}