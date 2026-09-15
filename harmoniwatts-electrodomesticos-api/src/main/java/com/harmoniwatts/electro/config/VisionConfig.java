package com.harmoniwatts.electro.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(VisionProperties.class)
public class VisionConfig {}
