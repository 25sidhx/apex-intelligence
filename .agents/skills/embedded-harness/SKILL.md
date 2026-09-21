---
name: embedded-harness
description: Specialized embedded systems, firmware, drone robotics, and hardware development harness combining ECC engineering instincts, zero-fluff output, and TDD verification.
---

# Embedded & Drone Engineering Harness

## 1. Code Standards
- **Memory & Safety:** Explicit stack/heap allocations. Always check return codes (`esp_err_t`, `HAL_StatusTypeDef`, `rcl_ret_t`).
- **Pinouts & Hardware:** Declare all GPIOs, SPI/I2C frequencies, and DMA configurations in dedicated header/config blocks.
- **Timing:** Account for RTOS tick rates, interrupt latency, and non-blocking state machines.

## 2. Testing & Verification Workflow
1. Define test bench / mock interfaces (Unity, GoogleTest, or SITL in Gazebo).
2. Specify expected register bitmasks / timing diagrams.
3. Implement driver / node logic.
4. Verify with boundary conditions.

## 3. Output Format
- Direct code blocks with explicit target file paths.
- Step-by-step flash / build commands.
- Zero boilerplate filler.
