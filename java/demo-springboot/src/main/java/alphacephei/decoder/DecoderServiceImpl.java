package alphacephei.decoder;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.vosk.Model;
import org.vosk.Recognizer;

import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.UnsupportedAudioFileException;
import java.io.BufferedInputStream;
import java.io.IOException;

@Service
@RequiredArgsConstructor
public class DecoderServiceImpl implements DecoderService {

    private static final int SAMPLE_RATE = 16000;
    private final Model model;

    @Override
    public ResponseDTO detect(MultipartFile wav, int wavSize) {
        try (AudioInputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(wav.getInputStream()));
             Recognizer recognizer = new Recognizer(model, SAMPLE_RATE)) {

            byte[] b = new byte[wavSize];
            int nbytes = ais.read(b);

            recognizer.acceptWaveForm(b, nbytes);
            return new ResponseDTO(recognizer.getResult());
        } catch (
                UnsupportedAudioFileException | IOException e) {
            throw new RuntimeException(e);
        }
    }
}