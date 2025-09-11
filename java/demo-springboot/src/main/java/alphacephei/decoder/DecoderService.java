package alphacephei.decoder;

import org.springframework.web.multipart.MultipartFile;

public interface DecoderService {

    ResponseDTO detect(MultipartFile wav, int wavSize);
}
