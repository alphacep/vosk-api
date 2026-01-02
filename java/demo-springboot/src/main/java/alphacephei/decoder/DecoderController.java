package alphacephei.decoder;

import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class DecoderController {

    private final DecoderService decoderService;

    @PostMapping("/detect")
    public ResponseDTO detectWav(@RequestParam(name = "wav") @NotNull MultipartFile wav,
                                 @RequestParam(name = "wavSize") @NotNull int wavSize) {
        return decoderService.detect(wav, wavSize);
    }
}
