using System;

namespace Vosk
{
    public class VoskBatchRecognizer : System.IDisposable
    {
        private System.Runtime.InteropServices.HandleRef handle;

        internal VoskBatchRecognizer(System.IntPtr cPtr)
        {
            handle = new System.Runtime.InteropServices.HandleRef(this, cPtr);
        }

        internal static System.Runtime.InteropServices.HandleRef getCPtr(VoskBatchRecognizer obj)
        {
            return (obj == null) ? new System.Runtime.InteropServices.HandleRef(null, System.IntPtr.Zero) : obj.handle;
        }

        ~VoskBatchRecognizer()
        {
            Dispose(false);
        }

        public void Dispose()
        {
            Dispose(true);
            System.GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            lock (this)
            {
                if (handle.Handle != System.IntPtr.Zero)
                {
                    VoskPINVOKE.delete_VoskBatchRecognizer(handle);
                    handle = new System.Runtime.InteropServices.HandleRef(null, System.IntPtr.Zero);
                }
            }
        }

        public VoskBatchRecognizer(BatchModel model, float sample_rate) : this(VoskPINVOKE.new_VoskBatchRecognizer(BatchModel.getCPtr(model), sample_rate))
        {
        }

        public bool AcceptWaveform(byte[] data, int len)
        {
            return VoskPINVOKE.VoskBatchRecognizer_AcceptWaveform(handle, data, len);
        }

        private static string PtrToStringUTF8(System.IntPtr ptr)
        {
            int len = 0;
            while (System.Runtime.InteropServices.Marshal.ReadByte(ptr, len) != 0)
                len++;
            byte[] array = new byte[len];
            System.Runtime.InteropServices.Marshal.Copy(ptr, array, 0, len);
            return System.Text.Encoding.UTF8.GetString(array);
        }

        public string FrontResult()
        {
            return PtrToStringUTF8(VoskPINVOKE.VoskBatchRecognizer_FrontResult(handle));
        }

        public string Result()
        {
            string result = PtrToStringUTF8(VoskPINVOKE.VoskBatchRecognizer_FrontResult(handle));
            VoskPINVOKE.VoskBatchRecognizer_Pop(handle);
            return result;
        }

        public int GetNumPendingChunks()
        {
            return VoskPINVOKE.VoskBatchRecognizer_GetPendingChunks(handle);
        }

        public void FinishStream()
        {
            VoskPINVOKE.VoskBatchRecognizer_FinishStream(handle);
        }

        public void SetNLSML(bool nlsml)
        {
            VoskPINVOKE.VoskBatchRecognizer_SetNLSML(handle, Convert.ToInt32(nlsml));
        }
    }
}
