namespace Vosk {

public class Vosk {
  public static void SetLogLevel(int level) {
    VoskPINVOKE.SetLogLevel(level);
  }

  public static void GpuInit() {
    VoskPINVOKE.GpuInit();
  }

  public static void GpuThreadInit() {
    VoskPINVOKE.GpuThreadInit();
  }
}

}
