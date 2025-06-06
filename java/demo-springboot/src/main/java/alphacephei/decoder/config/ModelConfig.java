package alphacephei.decoder.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.vosk.Model;

import java.io.IOException;

@Configuration
public class ModelConfig {

    @Bean
    public Model getModel(@Value("${vosk.model.path}") String modelPath) throws IOException {
        return new Model(modelPath);
    }
}