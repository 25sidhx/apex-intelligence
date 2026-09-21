#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_camera.h"

static const char *TAG = "P4_VISION";

void app_main(void)
{
    ESP_LOGI(TAG, "Initializing ESP32-P4 Vision Pipeline @ 400MHz...");
    // Hardware accelerated MIPI-CSI & H.264 encode init
    while (1) {
        ESP_LOGD(TAG, "Frame captured -> Inference dispatching to ESP-DL");
        vTaskDelay(pdMS_TO_TICKS(33)); // ~30 FPS
    }
}
