using System;
using System.IO;
using Kaldi;

public class Test
{
   public static void Main()
   {

        Vosk.SetLogLevel(0);
        Model model = new Model("model");
        KaldiRecognizer rec = new KaldiRecognizer(model, 16000.0f);

        using(Stream source = File.OpenRead("test.wav")) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while((bytesRead = source.Read(buffer, 0, buffer.Length)) > 0) {
                if (rec.AcceptWaveform(buffer, bytesRead)) {
                    Console.WriteLine(rec.Result());
                } else {
                    Console.WriteLine(rec.PartialResult());
                }
            }
        }
        Console.WriteLine(rec.FinalResult());

        rec = new KaldiRecognizer(model, 16000.0f);

        using(Stream source = File.OpenRead("test.wav")) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while((bytesRead = source.Read(buffer, 0, buffer.Length)) > 0) {
                float[] fbuffer = new float[bytesRead / 2];
                for (int i = 0, n = 0; i < fbuffer.Length; i++, n+=2) {
                    fbuffer[i] = (short)(buffer[n] | buffer[n+1] << 8);
                }
                if (rec.AcceptWaveform(fbuffer, fbuffer.Length)) {
                    Console.WriteLine(rec.Result());
                    GC.Collect();
                } else {
                    Console.WriteLine(rec.PartialResult());
                }
            }
        }
        Console.WriteLine(rec.FinalResult());
   }
}
